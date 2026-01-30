# -*- coding: utf-8 -*-
# Compatible with  Python 2.6/2.7 and 3.x

print("Importing package 'assigment'...")

from ._set_instance         import InstanceSetter
from ._set_material         import MaterialSetter
from ._set_section          import SectionSetter
from ._set_section_assign   import SectionAssigner

Catalog = {
    '_inst'     :InstanceSetter,
    '_mat'      :MaterialSetter,
    '_sec'      :SectionSetter,
    '_sec_a'    :SectionAssigner,
}

__all__ = [
    'InstanceSetter',
    'MaterialSetter',
    'SectionSetter',
    'SectionAssigner',
    "Catalog",
]
