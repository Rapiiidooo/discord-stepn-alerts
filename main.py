import secrets
from stepn import mapping_order, mapping_chain, mapping_type, StepnRequest, url_pics, mapping_quality_reversed, \
    mapping_chain_reversed, StepnNotFound
from stepn_discord import StepnClient

ID = secrets.ID
TOKEN = secrets.TOKEN
PUBLIC = secrets.PUBLIC

STEPN_ACCOUNT = secrets.STEPN_ACCOUNT
STEPN_PASSWORD = secrets.STEPN_PASSWORD

rules_to_check = [
    # Check lowest price of any shoes:
    {
        "title": "Floor price under 1 sol",
        "conditions": f"%sellPrice < 1500000",
        "params": {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,  # use int here
            "type": mapping_type["sneakers_all"],
        },
        "page_end": 0,  # use int here
        "limit": 2,  # use int here
    },
    {
        "title": "Floor price above 2 sol",
        "conditions": f"%sellPrice > 2000000",
        "params": {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,  # use int here
            "type": mapping_type["sneakers_all"],
        },
        "page_end": 0,  # use int here
        "limit": 2,  # use int here
    },

    # Check min luck = 10
    # {
    #     "title": "Shoes with at least luck > 10 !",
    #     "conditions": f"%sellPrice < 1500000",
    #     "conditions_on_stats": f"%attr.Luck > 100",
    #     "params": {
    #         "order": mapping_order["lowest_price"],
    #         "chain": mapping_chain["sol"],
    #         "refresh": "true",
    #         "page": 0,
    #         "type": mapping_type["sneakers_all"],
    #     },
    #     "page_end": 0,
    #     "limit": 3,
    # },
]

messages_dict = {
    "mention": "stepnwatcher",
    "messages": [],
}


def main():
    stepn = StepnRequest(email=STEPN_ACCOUNT, password=STEPN_PASSWORD)
    for item in rules_to_check:
        title = item.get("title") + '\n' if item.get("title") else ''
        page = item.get("params").get("page")
        limit = item.get("limit")

        nb_matched = 0
        while page <= item["page_end"]:
            rows = stepn.get_orderlist(**item["params"]).get("data")
            # stop condition
            page += 1

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
                    message += title + \
                               f"Id: {row.get('id')}\n" + \
                               f"Prix: {row.get('sellPrice') / 1000000} {mapping_chain_reversed[item.get('params').get('chain')]}\n" + \
                               f"Level: {row.get('level')}\n" + \
                               f"Quality: {mapping_quality_reversed[row.get('quality')]}\n" + \
                               f"Minted: {row.get('mint')}\n"

                if conditions_on_stats := item.get("conditions_on_stats"):
                    try:
                        details = stepn.get_orderdata(order_id=row.get('id'))

                        conditions_on_stats = stepn.replace_detail_binded_vars(conditions=conditions_on_stats,
                                                                               row=details)

                        if conditions_on_stats and eval(conditions_on_stats):
                            message += f"Efficiency: {stepn.get_orderdata_attrs(details, 'Efficiency')}\n" + \
                                       f"Luck: {stepn.get_orderdata_attrs(details, 'Luck')}\n" + \
                                       f"Comfort: {stepn.get_orderdata_attrs(details, 'Comfort')}\n" + \
                                       f"Resilience: {stepn.get_orderdata_attrs(details, 'Resilience')}\n" + \
                                       f"Unknown: {stepn.get_orderdata_attrs(details, 'Unknown')}\n"
                            nb_matched += 1
                        else:
                            message = None
                            image = None
                    except StepnNotFound:
                        print(f"Met order price but order {row.get('id')} already gone.")
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
