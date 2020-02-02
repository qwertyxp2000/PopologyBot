import praw
import re

popology_text = []
file_path = "commented.txt"
official_to_nicks = {}
popology_to_tower = []

def authenticate():
    print("Authenticating...\n")
    reddit = praw.Reddit("PopologyBot", user_agent="PopologyBot (by /u/RandyZ524)")
    print("Authenticated as {}\n".format(reddit.user.me()))
    return reddit


def main():
    global popology_text
    global official_to_nicks
    global popology_to_tower
    reddit = authenticate()
    subreddit = reddit.subreddit("test")
    popology_text = get_popology_info(reddit)
    official_to_nicks = get_tower_nicks()
    popology_to_tower = get_tower_categories()

    for comment in subreddit.comments(limit=250):
        match = re.findall(r'(?<=\[\[).+?(?=\]\])', comment.body)

        if match:
            process_comment(comment, match)


def get_tower_categories():
    popology_to_tower = [
        ["Dart Monkey", "Boomerang Monkey", "Bomb Shooter", "Tack Shooter", "Ice Monkey", "Glue Gunner"],
        ["Sniper Monkey", "Monkey Sub", "Monkey Buccaneer", "Monkey Ace", "Heli Pilot", "Mortar Monkey"],
        ["Wizard Monkey", "Super Monkey", "Ninja Monkey", "Alchemist", "Druid"],
        ["Banana Farm", "Spike Factory", "Monkey Village", "Engineer Monkey"],
        ["Quincy", "Gwendolin", "Striker Jones", "Obyn Greenfoot", "Captain Churchill", "Benjamin", "Ezili",
         "Pat Fusty", "Adora"]]
    return popology_to_tower


def get_popology_links():
    links = ["https://www.reddit.com/r/btd6/comments/atomg3/advanced_popology_vol_1_primary_towers/",
             "https://www.reddit.com/r/btd6/comments/ay2bnz/advanced_popology_vol_2_military_towers/",
             "https://www.reddit.com/r/btd6/comments/b6dudv/advanced_popology_vol_3_magic_towers/",
             "https://www.reddit.com/r/btd6/comments/bcxhmq/advanced_popology_vol_4_support_towers/",
             "https://www.reddit.com/r/btd6/comments/cfu359/advanced_popology_vol_5_heroes/"]
    return links


def get_submission_text(reddit, link):
    return reddit.submission(url=link).selftext


def get_popology_info(reddit):
    popology_text = []

    for link in get_popology_links():
        popology_text.append(get_submission_text(reddit, link))

    return popology_text


def get_tower_nicks():
    official_to_nicks = {}
    nick_file = open("tower_nicknames.txt", 'r')
    current_tower = ""

    for line in nick_file.read().splitlines():
        if not '    ' in line:
            official_to_nicks[line] = []
            current_tower = line
        else:
            official_to_nicks.get(current_tower).append(line.strip())

    return official_to_nicks


def update_old_comments(new_id):
    old_comments_w = open(file_path, 'a')
    old_comments_w.write(new_id + '\n')
    old_comments_w.close()


def parse_tower(pruned_name):
    for official, nicks in official_to_nicks.items():
        if pruned_name in nicks:
            return official

    return None


def calc_search_until(upgrade, path, temp):
    if int(upgrade) == 5:
        if path == 2:
            return "---"
        else:
            return "##"
    else:
        temp[path] = str(int(temp[path]) + 1)
        return ''.join(temp) + " — "


def get_info(pruned_name, parsed_upgrade, search_until, popology_text):
    print("\t\tTower's actual name: " + pruned_name)
    print("\t\tInfo starts at \"" + parsed_upgrade + " - \" found after \"" + pruned_name + "\"")
    print("\t\tInfo ends at \"" + search_until + "\" found after starting index")
    start_index = popology_text.index(parsed_upgrade + " — ", popology_text.index(pruned_name))
    end_index = popology_text.index(search_until, start_index)
    print("\t\tInfo between " + str(start_index) + " and " + str(end_index))
    return popology_text[start_index:end_index].strip()


def find_tower_category(tower):
    for i, category in enumerate(popology_to_tower):
        if tower in category:
            return i


def add_to_reply(upgrade, path, pruned_name):
    temp = list("000")
    temp[path] = upgrade
    parsed_upgrade = ''.join(temp)
    search_until = calc_search_until(upgrade, path, temp)
    info = get_info(pruned_name, parsed_upgrade, search_until, popology_text[find_tower_category(pruned_name)])

    if info[-1:] is '*':
        info = info[:-1].strip()

    return info + '\n'


def process_comment(comment, match):
    global popology_text
    global file_path
    print("Format found in comment with comment ID: " + comment.id)
    old_comments_r = open(file_path, 'r')

    if comment.id.strip() in old_comments_r.read().splitlines():
        print("Already replied to comment")
        return

    old_comments_r.close()
    print("Unique comment found, replying with info")
    print("Requests detected: " + str(match))
    reply = ""

    for tower in match:
        check_upgrades = tower.strip()[-3:]

        if len(re.findall(r'[1-5]', check_upgrades)) > 2 or len(re.findall(r'[3-5]', check_upgrades)) > 1:
            print('\t' + tower + " cannot be parsed")
            continue

        pruned_name = parse_tower(tower.strip()[:-3].lower().strip())

        if not pruned_name:
            print(tower.strip()[:-3].lower().strip() + " could not be identified")
            continue

        print('\t' + tower + " is being parsed")
        upgrades = list(check_upgrades)
        reply = reply + "## " + pruned_name + " (" + "".join(upgrades) + ")\n"
        print(reply)

        for path, upgrade in enumerate(upgrades, start=0):
            if int(upgrade) == 0:
                continue

            reply = reply + add_to_reply(upgrade, path, pruned_name)

    if reply:
        print(reply)
        comment.reply(reply.replace('\n', '\n\n'))
        update_old_comments(comment.id)


if __name__ == "__main__":
    main()
