import requests
from dataclasses import dataclass, asdict
from typing import List
from bs4 import BeautifulSoup
from tqdm import tqdm
import os

api_key = "0iVKSDmfcvLekS1QjsJRqpUaztocZ2eSFJD5gi29"
params = {"api_key": api_key, "format": "json", "limit": 50}
url = "https://api.congress.gov/v3/law/119"


@dataclass
class Law:
    title: str
    sponsor: List[str]
    actions: List[dict]
    text: str
    originChamberCode: str
    congress: int
    number: int

    def to_json(self) -> str:
        import json

        return json.dumps(asdict(self), indent=2)


# Make data directory if it does not exist
if not os.path.exists("data"):
    os.makedirs("data")


# Get all laws
bills = requests.get(url, params=params).json().get("bills")
# Get a bill
for bill_0 in tqdm(bills):
    bill = requests.get(bill_0.get("url"), params=params).json().get("bill")
    title = bill.get("title")
    sponsors = bill.get("sponsors")[0]
    originChamberCode = bill.get("originChamberCode")

    # Get member info
    member = requests.get(sponsors.get("url"), params=params).json().get("member")
    officialWebsiteUrl = member.get("officialWebsiteUrl")
    # Get most recent term first
    terms = member.get("terms")
    terms.reverse()

    state = member.get("state")
    name = member.get("directOrderName")
    bioguideId = member.get("bioguideId")

    sponsor = {
        "name": name,
        "websiteUrl": officialWebsiteUrl,
        "terms": terms,
        "state": state,
        "bioguideId": bioguideId,
    }

    number = bill.get("number")
    congress = bill.get("congress")

    # Get Bill actions
    actions = (
        requests.get(bill.get("actions").get("url"), params=params)
        .json()
        .get("actions")
    )
    actions.reverse()

    # Get Bill Text
    text = requests.get(bill.get("textVersions").get("url"), params=params).json()
    formats = text.get("textVersions")[0].get("formats")
    text = next((item for item in formats if item["type"] == "Formatted Text"), None)
    bill_text_raw = requests.get(text.get("url"))
    soup = BeautifulSoup(bill_text_raw.text, "html.parser")
    text = soup.find("pre").get_text().strip()
    law = Law(title, sponsor, actions, text, originChamberCode, congress, number)

    with open(f"data/{originChamberCode}.{congress}.{number}.json", "w") as f:
        f.write(law.to_json())
