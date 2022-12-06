class SimActions:
    MODIFY = "Modify"
    CREATE = "Create"
    RESOLVE = "Resolve"


class IemTicketFields:
    NOMINATED_SUPPORT_RESOURCES = "/customFields/full_text/nominated_support_resources"
    EVENT_DATE_FROM = "/customFields/date/event_date_from"
    EVENT_DATE_TO = "/customFields/date/event_date_to"

    @classmethod
    def all_related_fields(cls) -> set:
        list_of_class_attr = list()
        for attr in dir(cls):
            if attr[:2] != "__" and not isinstance(
                getattr(cls, attr), type(cls.all_related_fields)
            ):
                list_of_class_attr.append(getattr(cls, attr))
        return list_of_class_attr
