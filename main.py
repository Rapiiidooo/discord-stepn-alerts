import json

import secrets
from stepn import StepnRequest, url_pics, mapping_chain_reversed, StepnNotFound, \
    safe_evolution, safe_add_percent, safe_minus_percent, mapping_currency
from stepn_discord import StepnClient

DISCORD_ID = secrets.DISCORD_BOT_ID
DISCORD_TOKEN = secrets.DISCORD_BOT_TOKEN
DISCORD_PUBLIC = secrets.DISCORD_BOT_PUBLIC

STEPN_ACCOUNT = secrets.STEPN_ACCOUNT
STEPN_PASSWORD = secrets.STEPN_PASSWORD

GOOGLE_2AUTH = secrets.GOOGLE_2AUTH

rules_to_check = secrets.RULES

messages_dict = {
    "mention": "stepnwatcher",
    "messages": [],
}


def main():
    stop = False

    stepn = StepnRequest(email=STEPN_ACCOUNT, password=STEPN_PASSWORD, google_2auth_secret=GOOGLE_2AUTH)
    for item in rules_to_check:
        title = item.get("title") if item.get("title") else ''
        page = item.get("params").get("page")
        limit = item.get("limit", 1000)
        price = item.get("price")
        threshold = item.get("threshold")
        chain = mapping_chain_reversed[item.get('params').get('chain')]
        image_enabled = item.get("image_enabled")

        nb_matched = 0
        while page <= item["page_end"]:
            item["params"]["page"] = page

            # stop condition
            page += 1

            rows = stepn.get_orderlist(**item["params"])
            rows = rows.get("data") if rows else []

            if limit and "conditions_on_stats" not in item:
                rows = rows[:limit]

            # For every shoe's in dict
            for row in rows:
                message = ''
                image = ''

                row = stepn.reduce_item(details=row)

                conditions = item.get("conditions")
                conditions = stepn.replace_binded_vars(conditions=conditions, row=row)

                sell_price = row.get('sellPrice')

                if eval(conditions):
                    price_evolution = safe_evolution(row.get('sellPrice'), price, default=0)

                    print(price_evolution, threshold)

                    if (price_evolution and threshold and abs(price_evolution) > threshold) or not price:
                        image = f"{url_pics}/{row.get('img')}" if image_enabled else None
                        message = stepn.human_readable_stats(title=title, chain=chain, details=row)

                        if price:
                            message += f"\n{price_evolution}% from previous price, new price limit: "
                            message += f"{sell_price} ${mapping_currency[chain]} (+{safe_add_percent(sell_price, threshold)} ${mapping_currency[chain]}/-{safe_minus_percent(sell_price, threshold)} {mapping_currency[chain]}) ({threshold}%)"
                            with open(secrets.RATIO_FILENAME, 'w') as f:
                                new_price = {
                                    "price": row.get('sellPrice'),
                                    "threshold": threshold,
                                }
                                json.dump(new_price, f, indent=4)

                        with open("log.txt", "a") as log_file:
                            log_file.write(message)

                        stop = True

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

                if message and (image or not image_enabled):
                    print(message)
                    messages_dict["messages"].append((message, image))

                # This is for the details limit
                if nb_matched >= limit or stop:
                    page = item["page_end"] + 1
                    break
    return
    if messages_dict["messages"]:
        client = StepnClient(messages_dict=messages_dict)
        client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()
