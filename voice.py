import functions


def main():
    error = 0
    service = functions.authenticate_google()
    functions.speak('how can i help you')
    text = functions.get_audio().lower()
    text = text.replace("'", '')
    print(text)

    if 'add' in text or 'put' in text:
        functions.speak('what would you like me to add')
        text = functions.get_audio().lower()
        text = text.replace("'", '')
        print(text)
        date = functions.get_date(text)
        time = functions.get_time(text)
        description = functions.get_event_description(text)
        print(date, time, description)
        functions.add_to_calendar(date, time, description)

    else:
        for trigger in functions.triggers:
            if trigger in text:
                date = functions.get_date(text)
                if date:
                    functions.get_events(date, service)
                    break
            else:
                error += 1
                if error == len(functions.triggers):
                    functions.speak('Sorry, could you try again')


if __name__ == '__main__':
    main()
