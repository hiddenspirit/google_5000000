#!/usr/bin/env python3

import codecs
import glob
import re


LEAK_FILE = "google_5000000.txt"
CONTACT_FILE_TYPES = ["*.csv", "*.vcf"]
DEFAULT_DOMAIN = "gmail.com"

EMAIL_ADDRESS_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}", re.I)
LOCAL_PART_RE = re.compile(r"\b[a-z0-9._%+-]+\b", re.I)


def get_encoding(file, default=None):
    with open(file, "rb") as f:
        buf = f.read(len(codecs.BOM_UTF32))
    if buf.startswith(codecs.BOM_UTF8):
        encoding = "utf-8-sig"
    elif (buf.startswith(codecs.BOM_UTF16_LE) or
          buf.startswith(codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    elif (buf.startswith(codecs.BOM_UTF32_LE) or
          buf.startswith(codecs.BOM_UTF32_BE)):
        encoding = "utf-32"
    else:
        encoding = default
    return encoding


class EmailAddressesSet(set):
    @classmethod
    def normalize(cls, email_address):
        email_address = email_address.replace("–", "-")
        email_address = email_address.lower()
        return email_address

    def add(self, elem):
        super().add(self.normalize(elem))


leaked_email_addresses = EmailAddressesSet()
contact_email_addresses = EmailAddressesSet()

print("Loading leaked email addresses from {!r}...".format(LEAK_FILE))
with open(LEAK_FILE, encoding=get_encoding(LEAK_FILE, "cp1252")) as f:
    for line in f:
        match_count = 0
        for match in EMAIL_ADDRESS_RE.finditer(line):
            email_address = match.group()
            leaked_email_addresses.add(email_address)
            match_count += 1
        if not match_count:
            for match in LOCAL_PART_RE.finditer(line):
                email_address = "{}@{}".format(match.group(), DEFAULT_DOMAIN)
                if EMAIL_ADDRESS_RE.match(email_address):
                    leaked_email_addresses.add(email_address)
                else:
                    print("No email address on this line: {!r}".format(line))

for contacts_file_type in CONTACT_FILE_TYPES:
    contacts_count = 0
    for contacts_file in glob.glob(contacts_file_type):
        with open(contacts_file, encoding=get_encoding(contacts_file)) as f:
            for line in f:
                for match in EMAIL_ADDRESS_RE.finditer(line):
                    email_address = match.group()
                    contact_email_addresses.add(email_address)
                    contacts_count += 1
        print("{} contacts loaded from from {!r}.".format(contacts_count,
                                                            contacts_file))

print()
print("Leaked email addresses that are in your contacts:")
leaked_count = 0
for email_address in sorted(contact_email_addresses):
    if email_address in leaked_email_addresses:
        leaked_count += 1
        print(email_address)
print("Total: {}".format(leaked_count))
input("Press any key.")
