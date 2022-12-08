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
        return get_all_class_attr(cls, cls.all_related_fields)


class Profiles:
    LINUX = "Linux"
    WINDOWS = "Windows"
    NETWORKING = "Networking"
    DATABASE = "Database"
    DEPLOYMENT = "Deployment"
    ANALYTICS = "Analytics"
    BIG_DATA = "Big Data"
    SCD = "SCD"
    DMS = "DMS"
    SECURITY = "Security"

    @classmethod
    def all_profiles(cls) -> set:
        return get_all_class_attr(cls, cls.all_profiles)


def get_all_class_attr(cls, class_method_exception) -> set:
    list_of_class_attr = set()
    for attr in dir(cls):
        if attr[:2] != "__" and not isinstance(getattr(cls, attr), type(class_method_exception)):
            list_of_class_attr.add(getattr(cls, attr))
    return list_of_class_attr
