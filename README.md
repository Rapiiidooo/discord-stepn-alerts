# discord-stepn-alerts

Python bot to obtain alert price in stepn marketplace

# Rust lib: stepn-password

is a fork of https://github.com/Numenorean/stepn-password

# Build the lib

```
pip3 install virtualenv
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt

maturin develop
```

# Dependencies

- Rust
- Python >=3.10

# secret.py example

```
ID = "1000000000000000000"
TOKEN = "..."
PUBLIC = "..."

STEPN_ACCOUNT = "user@mail.com"
STEPN_PASSWORD = "password"

RULES = [
    {
        "title": "Any shoes under 2 $GMT",
        "conditions": f"%sellPrice < 2000000",
        "params": {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,
            "type": mapping_type["sneakers_all"],
        },
        "page_end": 0,
        "limit": 2,
    },

    Check min luck = 10
    {
        "title": "Shoes with at least luck > 10 !",
        "conditions": f"%sellPrice < 1500000",
        "conditions_on_stats": f"%attr.Luck > 100",
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
]
```

# Public

For the ready to use bot:

Create the following role : `stepnwatcher`
Create the following channel: `stepn-marketplace`

Invite the bot with minimum of write rights and roles usage:

https://discord.com/api/oauth2/authorize?client_id=1000748328490893422&permissions=154890923024&scope=bot

If I have the time I'll create the dashboard to customize your alerts. But for now, you'll just receive the same as
mine.

Every price changing more than `"threshold": 15`%