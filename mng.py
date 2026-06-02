"""Module for sending quest solutions to the mng.quest API."""
import requests  # type: ignore
from sys import argv


def send(quest_id: int) -> None:
    """
    Run the solver for the given quest_id
    """
    with open("./token.txt", "r", encoding="utf-8") as file:
        token = file.read()

    url = f"https://mng.quest/api/quest/{quest_id}/solve"
    quest_id_str = str(quest_id).zfill(2)
    rules_path = f"./quests/quest_{quest_id_str}.rules"
    with open(rules_path, "r", encoding="utf-8") as rules_file:
        rules = rules_file.read()

    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"instructions": rules},
    )

    data = response.json()
    if response.ok:
        print(data["msg"],
              "Leaderboard position:",
              data["leaderboard_position"])
    else:
        print("Error:",
              data["error"])


if __name__ == "__main__":
    send(int(argv[1]))
