import json

import secrets
from stepn import StepnRequest, url_pics, mapping_quality_reversed, mapping_chain_reversed, StepnNotFound, \
    safe_evolution, url_front
from stepn_discord import StepnClient

ID = secrets.ID
TOKEN = secrets.TOKEN
PUBLIC = secrets.PUBLIC

STEPN_ACCOUNT = secrets.STEPN_ACCOUNT
STEPN_PASSWORD = secrets.STEPN_PASSWORD

GOOGLE_2AUTH = secrets.GOOGLE_2AUTH

rules_to_check = secrets.RULES

messages_dict = {
    "mention": "stepnwatcher",
    "messages": [],
}


def main():
    stepn = StepnRequest(email=STEPN_ACCOUNT, password=STEPN_PASSWORD, google_2auth_secret=GOOGLE_2AUTH)
    for item in rules_to_check:
        title = item.get("title") + ' - ' if item.get("title") else ''
        page = item.get("params").get("page")
        limit = item.get("limit", 1000)
        price = item.get("ratio_price")
        threshold = item.get("ratio_threshold")

        nb_matched = 0
        while page <= item["page_end"]:
            item["params"]["page"] = page

            # stop condition
            page += 1

            rows = stepn.get_orderlist(**item["params"])
            rows = rows.get("data") if rows else []

            if limit and "conditions_on_stats" not in item:
                rows = rows[:limit]

            # For every shoes in dict
            for row in rows:
                message = ''
                image = ''

                conditions = item.get("conditions")
                conditions = stepn.replace_binded_vars(conditions=conditions, row=row)

                if eval(conditions):
                    image = f"{url_pics}/{row.get('img')}"
                    message += f"{url_front}/order/{row.get('id')}\n" + \
                               f"{title}" + \
                               f"{row.get('sellPrice') / 1000000} {mapping_chain_reversed[item.get('params').get('chain')]} - " + \
                               f"lvl {row.get('level')} - " + \
                               f"{mapping_quality_reversed[row.get('quality')]} - " + \
                               f"{row.get('mint')} mint"

                    evo = safe_evolution(row.get('sellPrice'), price, default=0)
                    if evo and threshold and abs(evo) > threshold:
                        message += f"Price is {evo}% different than the rule watcher. New price limit set to {row.get('sellPrice')}."
                        with open(secrets.RATIO_FILENAME, 'w') as f:
                            new_price = {
                                "price": row.get('sellPrice'),
                                "threshold": threshold,
                            }
                            json.dump(new_price, f, indent=4)

                        with open("log.txt", "a") as log_file:
                            log_file.write(message)

                        break

                if conditions_on_stats := item.get("conditions_on_stats"):
                    try:
                        details = stepn.get_orderdata(order_id=row.get('id'))

                        conditions_on_stats = stepn.replace_detail_binded_vars(
                            conditions=conditions_on_stats,
                            row=details
                        )

                        message += f" - " + \
                                   f"{stepn.get_orderdata_attrs(details, 'Efficiency') / 10} eff - " + \
                                   f"{stepn.get_orderdata_attrs(details, 'Luck') / 10} luck - " + \
                                   f"{stepn.get_orderdata_attrs(details, 'Comfort') / 10} com - " + \
                                   f"{stepn.get_orderdata_attrs(details, 'Resilience') / 10} res\n"

                        with open("log.txt", "a") as log_file:
                            log_file.write(message)

                        if conditions_on_stats and eval(conditions_on_stats):
                            log_file.write('MATCHED!')
                            nb_matched += 1
                        else:
                            message = None
                            image = None
                    except StepnNotFound:
                        print(f"Met conditions but order {row.get('id')} is already gone.")
                        message = None
                        image = None

                if message and image:
                    messages_dict["messages"].append((message, image))

                # This is for the details limit
                if nb_matched >= limit:
                    page = item["page_end"] + 1
                    break

    client = StepnClient(messages_dict=messages_dict)
    client.run(TOKEN)


if __name__ == '__main__':
    main()
