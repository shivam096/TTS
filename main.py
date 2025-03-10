from chatbot.SQLChatbot import SQLChatbot


def main():
    """Entry point for the Text-to-SQL chatbot."""
    chatbot = SQLChatbot()
    try:
        chatbot.run()
    finally:
        chatbot.cleanup()


if __name__ == "__main__":
    main()