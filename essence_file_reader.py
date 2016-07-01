import xml.etree.ElementTree
import logging
import sys
import argparse
import textwrap

loglevel = logging.DEBUG
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
#logger.setLevel(loglevel)

default_macro_width = 60

def format_ccomment(pstr):
    out_str = "/*"
    # max line len is 80; sub 6 for /* */ chars
    if len(pstr) > 74:
        wrapped_str = textwrap.wrap(pstr, 77)
        out_str += "\n"
        for wstr in wrapped_str:
            out_str += " * "
            out_str += wstr
            out_str += "\n"
        out_str += " */"
    else:
        out_str += " "
        out_str += pstr
        out_str += " "
        out_str += "*/"

    return out_str

class XMLElement(object):
    def __init__(self, XMLElement, type_name):
        self.xml_element = XMLElement
        self.type = type_name

    def __get_xml_element__(self, field):
        if self.xml_element.find(field) is not None:
            return self.xml_element.find(field).text
        else:
            logger.debug("Missing " + field +  " Element in " + self.type)
            return None

    def get_name(self):
        return self.__get_xml_element__("Name")

    def get_value(self):
        return self.__get_xml_element__("Value")

    def get_id(self):
        return self.__get_xml_element__("ID")

    def get_offset(self):
        return self.__get_xml_element__("Offset")

    def get_width(self):
        return self.__get_xml_element__("Width")

    def get_address_unit(self):
        return self.__get_xml_element__("AddressUnit")

    def get_data_unit(self):
        return self.__get_xml_element__("DataUnit")

    def get_custom(self):
        return self.__get_xml_element__("Custom")

    def get_hidden(self):
        hidden = self.__get_xml_element__("Hidden")
        if hidden is not None:
            if hidden == "False":
                return False
            else:
                return True

    def get_no_shadow(self):
        hidden = self.__get_xml_element__("NoShadow")
        if hidden is not None:
            if hidden == "False":
                return False
            else:
                return True

    def get_long_description(self):
        return self.__get_xml_element__("LongDescription")

    def get_short_description(self):
        return self.__get_xml_element__("ShortDescription")

    def get_data_width(self):
        return self.__get_xml_element__("DataWidth")

    def get_max_val(self):
        return self.__get_xml_element__("MaxVal")

    def get_min_val(self):
        return self.__get_xml_element__("MinVal")


class EnumElementNode(object):
    element_name = "EnumerationElement"
    def __init__(self, XMLParentNode, XMLEnumFieldElement):
        self.parent = XMLParentNode
        xml_element = XMLElement(XMLEnumFieldElement, EnumElementNode.element_name)
        self.name = xml_element.get_name()
        value = xml_element.get_value()
        if len(value) > 2:
            if value[0] == "0" and value[1] == "b":
                self.value = hex(int(value[2:], 2))
            elif value[0] == "0" and value[1] == "x":
                self.value = hex(int(value[2:], 16))
        else:
            self.value = hex(int(value))
        self.custom = xml_element.get_custom()
        self.hidden = xml_element.get_hidden()
        self.id = xml_element.get_id()
        self.long_description = xml_element.get_long_description()
        self.short_description = xml_element.get_short_description()

    def __str__(self):
        return "Name       : " + self.name + "\n" + \
                "Value      : " + str(self.value) + "\n" + \
                "short desc : " + self.short_description + "\n" + \
                "long desc  : " + self.long_description + "\n" + \
                "hidden     : " + str(self.hidden) + "\n"

    def write_cdefine(self, filep, width=default_macro_width, tag=""):
        if self.name is not None and self.value is not None:
            macro_val = self.value
            macro = "#define "
            if tag != "":
                macro += tag
                macro += "_"
            if self.parent.name is not None and self.parent.name != "":
                macro += self.parent.name
                macro += "_"
            macro += self.name
            macro =  macro.ljust(width)
            filep.write(macro)
            filep.write(macro_val)
            filep.write("\n")

    def write_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            filep.write(format_ccomment(comment))
            filep.write("\n")

  
class BitFieldElement(object):
    element_name = "BitFieldElement"
    def __init__(self, XMLParentNode, XMLBitFieldElement):
        self.parent = XMLParentNode
        xml_element = XMLElement(XMLBitFieldElement, BitFieldElement.element_name)
        self.name = xml_element.get_name()
        self.custom = xml_element.get_custom()
        self.hidden = xml_element.get_hidden()
        self.id = xml_element.get_id()
        self.width = xml_element.get_width()
        self.offset = xml_element.get_offset()
        self.long_description = xml_element.get_long_description()
        self.short_description = xml_element.get_short_description()
        self.enum_elements = []
        xml_enum_elements = XMLBitFieldElement.findall(EnumElementNode.element_name)
        for xml_enum_element in xml_enum_elements:
            enum_element = EnumElementNode(self, xml_enum_element)
            if enum_element is not None:
                self.enum_elements.append(enum_element)

    def __str__(self):
        return "Name       : " + self.name + "\n" + \
                "Offset     : " + str(self.offset) + "\n" + \
                "Width      : " + str(self.width) + "\n" + \
                "short desc : " + self.short_description + "\n" + \
                "long desc  : " + self.long_description + "\n" + \
                "hidden     : " + str(self.hidden) + "\n"

    def write_cdefine(self, filep, width=default_macro_width, tag=""):
        if self.name is not None and self.offset is not None and self.width is not None:
            mask = hex(pow(2, int(self.width)) - 1)
            macro = "#define "
            if tag != "":
                macro += tag
                macro += "_"
            macro += self.name
            macro += "_MASK"
            macro =  macro.ljust(width)
            if int(self.offset) == 0:
                macro_val = str(mask)
            else:
                macro_val = "( " + str(mask) + " << " + self.offset + " )"

            filep.write(macro)
            filep.write(macro_val)
            filep.write("\n")

    def write_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            filep.write(format_ccomment(comment))
            filep.write("\n")


class RegisterMemElement(object):
    element_name = "RegMemElement"
    def __init__(self, XMLParentNode, XMLRegisterMemElement):
        self.parent = XMLParentNode
        xml_element = XMLElement(XMLRegisterMemElement, RegisterMemElement.element_name)
        self.name = xml_element.get_name()
        self.custom = xml_element.get_custom()
        self.hidden = xml_element.get_hidden()
        self.id = xml_element.get_id()
        self.data_width = xml_element.get_data_width()
        self.no_shadow = xml_element.get_no_shadow()
        self.offset = xml_element.get_offset()
        self.long_description = xml_element.get_long_description()
        self.short_description = xml_element.get_short_description()
        self.bit_field_elements = []
        xml_bit_field_elements = XMLRegisterMemElement.findall(BitFieldElement.element_name)
        for xml_bit_field in xml_bit_field_elements:
            bit_field_element = BitFieldElement(self, xml_bit_field)
            if bit_field_element is not None:
                self.bit_field_elements.append(bit_field_element)

    def __str__(self):
        return "Name       : " + self.name + "\n" + \
                "Offset     : " + str(self.offset) + "\n" + \
                "Data Width : " + str(self.data_width) + "\n" + \
                "short desc : " + self.short_description + "\n" + \
                "long desc  : " + self.long_description + "\n" + \
                "hidden     : " + str(self.hidden) + "\n"

    def write_cdefine(self, filep, width=default_macro_width, tag=""):
        if self.name is not None and self.offset is not None:
            macro_val = hex(int(self.offset))
            macro = "#define "
            if tag != "":
                macro += tag
                macro += "_"
            macro += self.name
            macro =  macro.ljust(width)
            filep.write(macro)
            filep.write(macro_val)
            filep.write("\n")

    def write_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            filep.write(format_ccomment(comment))
            filep.write("\n")


class RegisterMemSet(object):
    element_name = "RegMemSet"
    def __init__(self, XMLParentNode, XMLRegisterMemSet):
        self.parent = XMLParentNode
        xml_element = XMLElement(XMLRegisterMemSet, RegisterMemSet.element_name)
        self.name = xml_element.get_name()
        self.custom = xml_element.get_custom()
        self.hidden = xml_element.get_hidden()
        self.id = xml_element.get_id()
        self.long_description = xml_element.get_long_description()
        self.short_description = xml_element.get_short_description()
        self.address_unit = xml_element.get_address_unit()
        self.data_unit = xml_element.get_data_unit()
        self.regmem_elements = []
        xml_regmem_elements = XMLRegisterMemSet.findall(RegisterMemElement.element_name)
        for xml_regmem_element in xml_regmem_elements:
            regmem_element = RegisterMemElement(self, xml_regmem_element)
            if regmem_element is not None:
                self.regmem_elements.append(regmem_element)
            

    def __str__(self):
        return "Name       : " + self.name + "\n" + \
                "Data Unit  : " + str(self.data_unit) + "\n" + \
                "Addr Unit  : " + str(self.address_unit) + "\n" + \
                "short desc : " + self.short_description + "\n" + \
                "long desc  : " + self.long_description + "\n" + \
                "hidden     : " + str(self.hidden) + "\n"

    def write_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            filep.write(format_ccomment(comment))
            filep.write("\n")


class EssenceFileReader(object):

    def __init__(self, essence_file_xml):
        self.essence_file_xml = essence_file_xml
        self._xml_root = xml.etree.ElementTree.parse(essence_file_xml).getroot()
        self.regmem_sets = []

        # generate regmem sets
        xml_regmem_sets = self._xml_root.findall(RegisterMemSet.element_name)
        for xml_regmem_set in xml_regmem_sets:
            regmem_set = RegisterMemSet(self._xml_root, xml_regmem_set)
            self.regmem_sets.append(regmem_set)

    def generate_header_file(self, outfile, product_tag):
        for regmem_set in self.regmem_sets:
            regmem_set.write_ccomment(outfile)
            for regmem_element in regmem_set.regmem_elements:
                regmem_element.write_ccomment(outfile)
                regmem_element.write_cdefine(outfile, tag=product_tag)
                for bit_field_element in regmem_element.bit_field_elements:
                    bit_field_element.write_ccomment(outfile)
                    bit_field_element.write_cdefine(outfile)
                    for enum_element in bit_field_element.enum_elements:
                        #enum_element.write_ccomment(outfile)
                        enum_element.write_cdefine(outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', action="store", help="prefix tag for register names", dest="product_tag", default="")
    parser.add_argument('-i', metavar='in-file', type=argparse.FileType('rt'))
    parser.add_argument('-o', metavar='out-file', type=argparse.FileType('wt'))
    results = parser.parse_args()
    reader = EssenceFileReader(results.i)
    reader.generate_header_file(results.o, results.product_tag)

        
