"""Simple NLP apparel ecommerce chatbot with ChatterBot."""

from pathlib import Path

from chatterbot import ChatBot
from chatterbot.tagging import LowercaseTagger
from chatterbot.trainers import ListTrainer


PRODUCT_WORDS = {
    "shirt": "shirt",
    "shirts": "shirt",
    "hoodie": "hoodie",
    "hoodies": "hoodie",
}

COLOR_WORDS = ["black", "white", "blue"]

SIZE_WORDS = {
    "xs": "xs",
    "extra small": "xs",
    "s": "s",
    "small": "s",
    "m": "m",
    "medium": "m",
    "l": "l",
    "large": "l",
}

SIZE_KEYS = sorted(SIZE_WORDS, key=len, reverse=True)

SAMPLE_INVENTORY = [
    ("shirt", "black", "m", 10),
    ("shirt", "white", "s", 5),
    ("hoodie", "blue", "l", 3),
]

SAMPLE_ORDERS = {
    "12345": "shipped",
    "67890": "processing",
}

UNKNOWN_QUESTIONS = "I did not understand that request, sorry. Can you please rephrase?"
CHATBOT_DB = Path(__file__).with_name("apparel_chatterbot.sqlite3")

TRAINING_CONVERSATIONS = [
    ["hello", "Hi there! How can I assist you with our apparel store today?"],
    ["hi", "Hi there! How can I assist you with our apparel store today?"],
    ["what do you sell", "We sell shirts and hoodies in black, white, and blue."],
    ["how long does shipping take", "Shipping typically takes 5-7 business days."],
    ["what is your return policy", "You can return any item within 30 days of purchase for a full refund."],
]

def new_state():
    return {"product": None}


def build_chatbot():
    return ChatBot(
        "EcommerceSupportBot",
        storage_adapter="chatterbot.storage.SQLStorageAdapter",
        database_uri="sqlite:///" + CHATBOT_DB.as_posix(),
        tagger=LowercaseTagger,
        read_only=True,
        preprocessors=["chatterbot.preprocessors.clean_whitespace"],
        logic_adapters=[
            {
                "import_path": "chatterbot.logic.BestMatch",
                "default_response": UNKNOWN_QUESTIONS,
                "maximum_similarity_threshold": 0.85,
            }
        ],
    )


def train_chatbot(chatbot):
    trainer = ListTrainer(chatbot, show_training_progress=False)
    for conversation in TRAINING_CONVERSATIONS:
        trainer.train(conversation)


def setup_chatbot():
    chatbot = build_chatbot()
    if chatbot.storage.count() == 0:
        train_chatbot(chatbot)
    return chatbot


def get_words(user_input):
    text = user_input.lower()
    for mark in ".,?!:;()[]{}\"'":
        text = text.replace(mark, " ")
    return text.split()


def has_phrase(words, phrase):
    phrase_words = phrase.split()
    length = len(phrase_words)
    for index in range(len(words)):
        if words[index:index + length] == phrase_words:
            return True
    return False


def find_size(words):
    for size_text in SIZE_KEYS:
        if has_phrase(words, size_text):
            return SIZE_WORDS[size_text]
    return None


def lookup_inventory(product, color, size):
    for item_product, item_color, item_size, item_stock in SAMPLE_INVENTORY:
        if item_product == product and item_color == color and item_size == size:
            return item_stock
    return None


def should_use_chatterbot(words):
    for word in words:
        if word in [
            "hello",
            "hi",
            "sell",
            "products",
            "items",
            "shipping",
            "delivery",
            "return",
            "returns",
            "refund",
        ]:
            return True
    return False


def extract_actionable_data(user_input, state):
    words = get_words(user_input)
    product = None
    color = None
    size = find_size(words)
    order_id = None

    for word in words:
        if product is None and word in PRODUCT_WORDS:
            product = PRODUCT_WORDS[word]
        if color is None and word in COLOR_WORDS:
            color = word
        if order_id is None and word.isdigit() and len(word) >= 4:
            order_id = word

    if product is None and (color is not None or size is not None):
        product = state["product"]

    if order_id is not None or "order" in words or "track" in words:
        intent = "order"
    elif product is not None:
        intent = "inventory"
    else:
        intent = "general"

    return {
        "intent": intent,
        "product": product,
        "color": color,
        "size": size,
        "order_id": order_id,
    }


def generate_response(user_input, chatbot, state=None):
    if state is None:
        state = new_state()

    data = extract_actionable_data(user_input, state)
    words = get_words(user_input)

    if data["product"] is not None:
        state["product"] = data["product"]

    if data["intent"] == "order":
        if data["order_id"] is None:
            return "Please enter your order ID."

        status = SAMPLE_ORDERS.get(data["order_id"])
        if status is None:
            return "Sorry, we could not find an order with that ID."

        return "Order " + data["order_id"] + " status: " + status

    if data["intent"] == "inventory":
        if data["color"] is None or data["size"] is None:
            return "What color and size are you looking for?"

        stock = lookup_inventory(data["product"], data["color"], data["size"])
        if stock is None:
            return "Sorry, we do not have that item in stock."

        return (
            "We have "
            + str(stock)
            + " "
            + data["color"]
            + " "
            + data["product"]
            + "s in size "
            + data["size"]
            + " available."
        )

    if not should_use_chatterbot(words):
        return UNKNOWN_QUESTIONS

    response = chatbot.get_response(user_input)
    if float(getattr(response, "confidence", 0) or 0) < 0.20:
        return UNKNOWN_QUESTIONS
    return str(response)


def main():
    chatbot = setup_chatbot()
    state = new_state()

    print("EcommerceSupportBot: Hi! Ask me a question about our apparel store.")
    print("EcommerceSupportBot: Type 'quit' to stop chatting.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            print("EcommerceSupportBot: Goodbye!")
            break
        print("EcommerceSupportBot: " + generate_response(user_input, chatbot, state))


if __name__ == "__main__":
    main()
