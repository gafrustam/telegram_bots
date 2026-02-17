"""Seed the topic_bank table with real IELTS exam topics.

Run once: python seed_topics.py
Requires DATABASE_URL env var.
"""
import asyncio
import json
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# ── Part 1 topics (everyday/personal) ──────────────────
PART1_TOPICS = [
    ("Home & accommodation", 1.2),
    ("Work", 1.2),
    ("Studies & education", 1.2),
    ("Hometown", 1.2),
    ("Family", 1.0),
    ("Friends", 1.0),
    ("Daily routine", 1.0),
    ("Food & cooking", 1.1),
    ("Weather & seasons", 1.0),
    ("Transport", 1.0),
    ("Shopping", 0.9),
    ("Hobbies & leisure", 1.1),
    ("Music", 1.0),
    ("Reading & books", 1.0),
    ("Movies & TV", 0.9),
    ("Sports & exercise", 1.0),
    ("Travel & holidays", 1.1),
    ("Technology & gadgets", 1.1),
    ("Internet & social media", 1.1),
    ("Clothes & fashion", 0.9),
    ("Health & fitness", 1.0),
    ("Animals & pets", 0.8),
    ("Nature & parks", 0.8),
    ("Photography", 0.8),
    ("Art & museums", 0.8),
    ("Neighbours & neighbourhood", 0.9),
    ("Languages & learning", 1.0),
    ("Flowers & gardens", 0.7),
    ("Birthdays & celebrations", 0.8),
    ("Time management", 0.9),
    ("Sleep & rest", 0.8),
    ("Colours", 0.7),
    ("Numbers & maths", 0.7),
    ("Happiness", 0.8),
    ("Patience", 0.7),
    ("Maps & directions", 0.7),
    ("Handwriting & pens", 0.7),
    ("Mirrors", 0.6),
    ("Stars & space", 0.7),
    ("Water & swimming", 0.7),
    ("Mornings & evenings", 0.7),
    ("Public transport", 0.9),
    ("Mobile phones", 1.0),
    ("Computers", 0.9),
    ("Emails & letters", 0.8),
    ("Weekends", 0.9),
    ("Noise", 0.7),
    ("Concentration & focus", 0.7),
    ("Gifts & presents", 0.8),
    ("Punctuality", 0.7),
]

# ── Part 2 topics (cue card monologues) ────────────────
PART2_TOPICS = [
    ("A memorable trip", 1.2, "Describe a memorable trip you took.\n\nYou should say:\n- where you went\n- who you went with\n- what you did there\n\nand explain why this trip was memorable."),
    ("A person who influenced you", 1.1, "Describe a person who has had a great influence on your life.\n\nYou should say:\n- who this person is\n- how you know them\n- what they have done\n\nand explain how they have influenced you."),
    ("A book you enjoyed reading", 1.0, "Describe a book you enjoyed reading.\n\nYou should say:\n- what the book was about\n- when you read it\n- why you chose to read it\n\nand explain what you particularly enjoyed about it."),
    ("A skill you learned", 1.1, "Describe a skill you learned that you are proud of.\n\nYou should say:\n- what the skill is\n- how you learned it\n- how long it took to learn\n\nand explain why you are proud of this skill."),
    ("A place you like to visit", 1.0, "Describe a place you like to visit in your free time.\n\nYou should say:\n- where the place is\n- how often you go there\n- what you do there\n\nand explain why you enjoy visiting this place."),
    ("An important decision", 1.1, "Describe an important decision you made.\n\nYou should say:\n- what the decision was\n- when you made it\n- how you made the decision\n\nand explain how you felt about it afterwards."),
    ("A childhood memory", 1.0, "Describe a happy childhood memory.\n\nYou should say:\n- what the memory is about\n- how old you were\n- who was involved\n\nand explain why this memory is special to you."),
    ("A piece of technology", 1.1, "Describe a piece of technology you find useful.\n\nYou should say:\n- what it is\n- how you use it\n- how long you have had it\n\nand explain why it is useful to you."),
    ("An achievement you are proud of", 1.0, "Describe an achievement you are proud of.\n\nYou should say:\n- what you achieved\n- when it happened\n- how you achieved it\n\nand explain why you are proud of this achievement."),
    ("A festival or celebration", 1.0, "Describe a festival or celebration that is important in your country.\n\nYou should say:\n- what the festival is\n- when it takes place\n- what people do during it\n\nand explain why it is important."),
    ("A time you helped someone", 0.9, "Describe a time when you helped someone.\n\nYou should say:\n- who you helped\n- what you helped them with\n- how you helped them\n\nand explain how you felt about helping."),
    ("A movie you enjoyed", 0.9, "Describe a movie you really enjoyed.\n\nYou should say:\n- what the movie was\n- what it was about\n- when and where you watched it\n\nand explain why you enjoyed it."),
    ("A challenge you overcame", 1.1, "Describe a challenge you faced and overcame.\n\nYou should say:\n- what the challenge was\n- when it happened\n- how you dealt with it\n\nand explain what you learned from the experience."),
    ("Your favourite meal", 0.9, "Describe your favourite meal.\n\nYou should say:\n- what the meal is\n- how it is prepared\n- how often you eat it\n\nand explain why it is your favourite."),
    ("A teacher who influenced you", 1.0, "Describe a teacher who had a positive influence on you.\n\nYou should say:\n- who this teacher was\n- what subject they taught\n- what made them special\n\nand explain how they influenced you."),
    ("A gift you received", 0.9, "Describe a gift you received that was special to you.\n\nYou should say:\n- what the gift was\n- who gave it to you\n- when you received it\n\nand explain why it was special to you."),
    ("A sport or physical activity", 0.9, "Describe a sport or physical activity you enjoy.\n\nYou should say:\n- what the activity is\n- when and where you do it\n- who you do it with\n\nand explain why you enjoy it."),
    ("A building you like", 0.8, "Describe a building you find interesting or beautiful.\n\nYou should say:\n- where the building is\n- what it looks like\n- what it is used for\n\nand explain why you find it interesting."),
    ("A time you were surprised", 0.9, "Describe a time when you were pleasantly surprised.\n\nYou should say:\n- what happened\n- when it happened\n- who was involved\n\nand explain why you were surprised."),
    ("A foreign culture you admire", 0.9, "Describe a foreign culture that you find interesting.\n\nYou should say:\n- what the culture is\n- how you learned about it\n- what aspects interest you\n\nand explain why you find this culture interesting."),
    ("An event that changed your life", 1.0, "Describe an event that changed your life.\n\nYou should say:\n- what the event was\n- when it happened\n- how it affected you\n\nand explain why it was a turning point."),
    ("A piece of advice you received", 0.9, "Describe a piece of good advice someone gave you.\n\nYou should say:\n- who gave you the advice\n- what the advice was\n- when you received it\n\nand explain how it helped you."),
    ("A historical place", 0.9, "Describe a historical place you have visited or would like to visit.\n\nYou should say:\n- where the place is\n- what is historically significant about it\n- how you learned about it\n\nand explain why you find it interesting."),
    ("A time you had to wait", 0.8, "Describe a time when you had to wait for a long time.\n\nYou should say:\n- what you were waiting for\n- where you waited\n- how long you waited\n\nand explain how you felt about waiting."),
    ("A successful small business", 0.8, "Describe a successful small business you know about.\n\nYou should say:\n- what the business is\n- how you know about it\n- what makes it successful\n\nand explain why you think it is a good business."),
    ("A creative person you admire", 0.9, "Describe a creative person you admire.\n\nYou should say:\n- who this person is\n- what they create\n- how you know about them\n\nand explain why you admire their creativity."),
    ("An item of clothing you like", 0.7, "Describe an item of clothing you particularly like.\n\nYou should say:\n- what it is\n- where you got it\n- when you wear it\n\nand explain why you like it."),
    ("A hobby you would like to try", 0.8, "Describe a hobby or activity you would like to try.\n\nYou should say:\n- what the hobby is\n- how you heard about it\n- what you would need to start\n\nand explain why you want to try it."),
    ("A difficult work or study situation", 0.9, "Describe a difficult situation you experienced at work or while studying.\n\nYou should say:\n- what the situation was\n- when it happened\n- what you did\n\nand explain what you learned from it."),
    ("A song or piece of music", 0.8, "Describe a song or piece of music you really like.\n\nYou should say:\n- what the song or music is\n- when you first heard it\n- how often you listen to it\n\nand explain why you like it."),
    ("A time you taught someone", 0.8, "Describe a time when you taught something to someone.\n\nYou should say:\n- who you taught\n- what you taught them\n- how you taught them\n\nand explain how successful the teaching was."),
    ("A place in nature", 0.9, "Describe a beautiful place in nature you have visited.\n\nYou should say:\n- where it is\n- when you visited\n- what you did there\n\nand explain why you found it beautiful."),
    ("A change you made in your life", 1.0, "Describe a positive change you made in your life.\n\nYou should say:\n- what the change was\n- when you made the change\n- why you decided to make it\n\nand explain how it improved your life."),
    ("An interesting conversation", 0.8, "Describe an interesting conversation you had recently.\n\nYou should say:\n- who you spoke with\n- what you talked about\n- where the conversation took place\n\nand explain why it was interesting."),
    ("A plan for the future", 0.9, "Describe a plan you have for the future.\n\nYou should say:\n- what the plan is\n- how you intend to achieve it\n- who might be involved\n\nand explain why this plan is important to you."),
    ("A website you use often", 0.8, "Describe a website or app you use regularly.\n\nYou should say:\n- what the website or app is\n- how often you use it\n- what you use it for\n\nand explain why you find it useful."),
    ("A time you got lost", 0.7, "Describe a time when you got lost.\n\nYou should say:\n- where you were going\n- how you got lost\n- what you did to find your way\n\nand explain how you felt about the experience."),
    ("A family tradition", 0.8, "Describe a tradition in your family.\n\nYou should say:\n- what the tradition is\n- how often it happens\n- who takes part in it\n\nand explain why this tradition is important to your family."),
    ("An environmental problem", 0.9, "Describe an environmental problem in your area.\n\nYou should say:\n- what the problem is\n- what causes it\n- how it affects people\n\nand explain what could be done to solve it."),
    ("A time you disagreed with someone", 0.8, "Describe a time when you disagreed with someone.\n\nYou should say:\n- who you disagreed with\n- what the disagreement was about\n- how you resolved it\n\nand explain what you learned from the experience."),
]

# ── Part 3 topics (abstract discussion) ────────────────
PART3_TOPICS = [
    ("Education & learning", 1.2),
    ("Technology & society", 1.2),
    ("Environment & sustainability", 1.1),
    ("Health & wellbeing", 1.0),
    ("Work & career", 1.1),
    ("Globalization & culture", 1.0),
    ("Media & information", 1.0),
    ("Housing & urban development", 0.9),
    ("Transport & infrastructure", 0.9),
    ("Family & relationships", 1.0),
    ("Crime & justice", 0.8),
    ("Tourism & travel impact", 0.9),
    ("Government & public services", 0.9),
    ("Arts & creativity", 0.9),
    ("Traditions & modernity", 1.0),
    ("Advertising & consumerism", 0.9),
    ("Ageing & elderly care", 0.8),
    ("Gender roles & equality", 0.9),
    ("Food & agriculture", 0.8),
    ("Communication & language", 0.9),
    ("Success & ambition", 0.9),
    ("Youth & generation gap", 0.9),
    ("Science & innovation", 1.0),
    ("Volunteering & community", 0.8),
    ("Money & economy", 0.9),
    ("Privacy & surveillance", 0.8),
    ("Leadership & decision-making", 0.8),
    ("Sport & competition", 0.8),
    ("History & heritage", 0.8),
    ("Artificial intelligence & automation", 1.0),
]


async def seed():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set")
        return

    conn = await asyncpg.connect(dsn)

    # Part 1
    for topic, weight in PART1_TOPICS:
        await conn.execute(
            """
            INSERT INTO topic_bank (part, topic, weight)
            VALUES (1, $1, $2)
            ON CONFLICT (part, topic) DO UPDATE SET weight = EXCLUDED.weight
            """,
            topic, weight,
        )
    print(f"Seeded {len(PART1_TOPICS)} Part 1 topics")

    # Part 2
    for topic, weight, cue_card in PART2_TOPICS:
        await conn.execute(
            """
            INSERT INTO topic_bank (part, topic, weight, cue_card)
            VALUES (2, $1, $2, $3)
            ON CONFLICT (part, topic) DO UPDATE SET weight = EXCLUDED.weight, cue_card = EXCLUDED.cue_card
            """,
            topic, weight, cue_card,
        )
    print(f"Seeded {len(PART2_TOPICS)} Part 2 topics")

    # Part 3
    for topic, weight in PART3_TOPICS:
        await conn.execute(
            """
            INSERT INTO topic_bank (part, topic, weight)
            VALUES (3, $1, $2)
            ON CONFLICT (part, topic) DO UPDATE SET weight = EXCLUDED.weight
            """,
            topic, weight,
        )
    print(f"Seeded {len(PART3_TOPICS)} Part 3 topics")

    await conn.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
