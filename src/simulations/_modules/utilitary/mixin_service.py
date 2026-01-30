from ..imports import *

class ServiceMixin(object):
    def __init__(self):
        pass
    def run(self):

        services_created = []

        for attr_name, ServiceClass in SERVICE_CATALOG.items():
            instance = ServiceClass()
            setattr(self, attr_name, instance)
            services_created.append(instance)

        self.propagate_to(*services_created)
