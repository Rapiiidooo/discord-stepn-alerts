import secrets
import stepn_discord
from stepn import mapping_order, mapping_chain, mapping_type, StepnRequest

ID = secrets.ID
TOKEN = secrets.TOKEN
PUBLIC = secrets.PUBLIC
AMOUNT_LIMIT = secrets.AMOUNT_LIMIT

rules_to_check = [
    # Check lowest price of any shoes:
    {
        "conditions": f"%sellPrice < {AMOUNT_LIMIT}",
        "params": {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,
            "type": mapping_type["sneakers_all"],
        },
        "page_end": 0,
        "limit": 3,
    },

    # Check min luck = 10
    {
        "conditions": f"%sellPrice < {AMOUNT_LIMIT}",
        "params": {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,
            "type": mapping_type["sneakers_all"],
            "gType": "",
            "quality": "",
            "level": "",
            "bread": "",
        },
        "page_end": 0,
        "limit": None
    },
]

messages_dict = {
    "mention": "stepnwatcher",
    "messages": [],
}
for item in rules_to_check:
    results = []

    page = item["params"]["page"]
    limit = item["params"]["limit"]
    conditions = item["params"]["conditions"]

    while int(page) <= int(item["page_end"]):
        results = StepnRequest.get_orderlist(**item["params"])

    if limit:
        results = results.get("data")[:limit]

    # For every shoes returned
    for result in results:

        # Replace all the binding vars
        while "%" in conditions:
            var_to_replace = conditions.split('%')[1].split()[0]
            conditions = conditions.replace(f"%{var_to_replace}", result.get(var_to_replace))

        if eval(conditions):
            messages_dict["messages"].append(
                f"""
                Id: {result.get('id')}\n
                Prix: {result.get('sellPrice') / 100000}\n
                """
            )

stepn_discord.client.run(TOKEN)
