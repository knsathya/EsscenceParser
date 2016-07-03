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

def format_cdefine(macro_name, macro_val, width=default_macro_width):
    macro = "#define "
    macro += macro_name
    macro = macro.ljust(width)
    macro += macro_val

    return macro

def unique_list(ilist):
    olist = []
    for item in ilist:
        if item not in olist or item == "MASK":
            olist.append(item)
    return olist

def remove_dup(l1, l2):
    for item in l1:
        if item in l2:
            l2.remove(item)

    return l2;

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
        self.tag = self.parent.tag
        self.long_description = xml_element.get_long_description()
        self.short_description = xml_element.get_short_description()

    def __str__(self):
        return "Name       : " + self.name + "\n" + \
                "Value      : " + str(self.value) + "\n" + \
                "short desc : " + self.short_description + "\n" + \
                "long desc  : " + self.long_description + "\n" + \
                "hidden     : " + str(self.hidden) + "\n"

    def get_cdefine(self, tag=""):
        if self.name is not None and self.value is not None:
            macro_val = self.value
            macro_name = []
            if tag != "":
                macro_name += tag.split('_')
            if self.tag is not None:
                macro_name += self.tag.split('_')
            if self.parent.name is not None and self.parent.name != "":
                macro_name  += remove_dup(macro_name, self.parent.name.split('_'))
            macro_name  += remove_dup(macro_name, self.name.split('_'))
            # handling some special cases
            if len(macro_name) > 0 and  macro_name[-1] == "MASK":
                macro_name[-1] = "VALUE"
            macro_name = "_".join(macro_name)
            return macro_name, macro_val

    def get_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            return comment

    def print_info(self):
        print "Enum Field Name :" + self.name
        self.parent.print_info()

  
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
        self.tag = self.parent.tag
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

    def get_cdefine(self, tag=""):
        if self.name is not None and self.offset is not None and self.width is not None:
            mask = hex(pow(2, int(self.width)) - 1)
            macro_name = []
            if tag != "":
                macro_name += tag.split('_')
            if self.tag is not None:
                macro_name += self.tag.split('_')
            macro_name  += remove_dup(macro_name, self.name.split('_'))
            macro_name.append("MASK")
            macro_name = "_".join(macro_name)
            if int(self.offset) == 0:
                macro_val = str(mask)
            else:
                macro_val = "( " + str(mask) + " << " + self.offset + " )"

            return macro_name, macro_val

    def get_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            return comment

    def print_info(self):
        print "Bit Field Name :" + self.name
        self.parent.print_info()


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
        self.tag = self.name
        if self.name is not None:
            name_list = self.name.split('_')
            if name_list.pop().startswith('REG'):
                if name_list[-1].startswith('IRQ'):
                    name_list.pop()
                self.tag = '_'.join(name_list)
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

    def get_cdefine(self, tag=""):
        if self.name is not None and self.offset is not None:
            macro_val = hex(int(self.offset))
            macro_name = ""
            if tag != "":
                macro_name += tag
                macro_name += "_"
            macro_name += self.name
            return macro_name, macro_val

    def get_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            return comment

    def print_info(self):
        print "Register Name :" + self.name
        self.parent.print_info()


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
        self.tag = self.name
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

    def get_ccomment(self, filep, tag=""):
        if self.short_description is not None and self.name is not None:
            comment = self.name
            comment += " : "
            comment += self.short_description
            return comment

    def print_info(self):
        print "RegMemSetName    :" + self.name

class EssenceFileReader(object):

    def __init__(self, essence_file_xml):
        self.essence_file_xml = essence_file_xml
        self._xml_root = xml.etree.ElementTree.parse(essence_file_xml).getroot()
        self.regmem_sets = []
        self.macro_sets = []

        # generate regmem sets
        xml_regmem_sets = self._xml_root.findall(RegisterMemSet.element_name)
        for xml_regmem_set in xml_regmem_sets:
            regmem_set = RegisterMemSet(self._xml_root, xml_regmem_set)
            self.regmem_sets.append(regmem_set)

    def _fix_macro_dup(self, max_index, cur_index, input_str):
        while True:
            new_macro_name = raw_input(input_str)
            is_duplicate = False
            for j in range(max_index):
                if self.macro_sets[j][2] is not None and self.macro_sets[j][2].strip() == new_macro_name:
                    is_duplicate = True
            if not is_duplicate:
                temp_set = list(self.macro_sets[cur_index])
                temp_set[2] = new_macro_name
                self.macro_sets[cur_index] = tuple(temp_set)
                break
            else:
                print "Duplicate entry found, enter new name"

    def _check_for_macro_dup(self):
        index = 0
        print "Number of lines: " + str(len(self.macro_sets))
        for macro_set in self.macro_sets:
            index += 1
            if macro_set[2] is not None:
                for i in range(index-1):
                    if self.macro_sets[i][2] is not None and self.macro_sets[i][2].strip() == macro_set[2].strip():
                        print "##########################################"
                        print "Found duplicate"
                        print "original: " + self.macro_sets[i][2]
                        self.macro_sets[i][0].print_info()
                        print "new: " + macro_set[2]
                        macro_set[0].print_info()
                        print "##########################################"
                        self._fix_macro_dup(index - 1, i, "Enter new macro name for original entry:")
                        self._fix_macro_dup(index - 1, self.macro_sets.index(macro_set), "Enter new macro name for new entry:")

    def generate_header_file(self, outfile, product_tag):
        for regmem_set in self.regmem_sets:
            comment = regmem_set.get_ccomment(outfile)
            self.macro_sets.append((regmem_set, comment, None, None))
            for regmem_element in regmem_set.regmem_elements:
                comment = regmem_element.get_ccomment(outfile)
                macro, macro_val = regmem_element.get_cdefine(tag=product_tag)
                self.macro_sets.append((regmem_element, comment, macro, macro_val))
                for bit_field_element in regmem_element.bit_field_elements:
                    comment = bit_field_element.get_ccomment(outfile)
                    macro, macro_val = bit_field_element.get_cdefine()
                    self.macro_sets.append((bit_field_element, comment, macro, macro_val))
                    for enum_element in bit_field_element.enum_elements:
                        #enum_element.get_ccomment(outfile)
                        macro, macro_val = enum_element.get_cdefine()
                        self.macro_sets.append((enum_element, None, macro, macro_val))

        self._check_for_macro_dup()

        for macroset in self.macro_sets:
            if macroset[1] is not None:
                outfile.write(format_ccomment(macroset[1]))
                outfile.write("\n")
            if macroset[2] is not None and macroset[3] is not None:
                outfile.write(format_cdefine(macroset[2], macroset[3]))
                outfile.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', action="store", help="prefix tag for register names", dest="product_tag", default="")
    parser.add_argument('-i', metavar='in-file', type=argparse.FileType('rt'))
    parser.add_argument('-o', metavar='out-file', type=argparse.FileType('wt'))
    results = parser.parse_args()
    reader = EssenceFileReader(results.i)
    reader.generate_header_file(results.o, results.product_tag)

        
