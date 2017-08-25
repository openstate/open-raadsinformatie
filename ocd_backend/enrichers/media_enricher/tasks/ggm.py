import string

from ocd_backend.enrichers.media_enricher.tasks import FileToText


class GegevensmagazijnFileToText(FileToText):
    def get_combined_index_data(self, media_item, content_type, file_object,
                                enrichment_data, object_id, combined_index_doc,
                                doc, doc_type):
        attachment = {
            '@type': "Attachment",
            'isBasedOn': media_item['original_url'],
        }
        if self.text:
            attachment['comment'] = media_item.get('note', u''),
            attachment['fileType'] = content_type,
            attachment['text'] = self.text
        else:
            attachment['comment'] = u'Unable to download or parse this file'

        if 'attachment' not in combined_index_doc:
            combined_index_doc['attachment'] = []
        combined_index_doc['attachment'].append(attachment)

        if 'attachment' not in doc:
            doc['attachment'] = []
        doc['attachment'].append(attachment)


class GegevensmagazijnMotionText(GegevensmagazijnFileToText):
    def process_text(self):
        lines = self.text.split("\n")

        # Determine in the first 10 lines if it is an actual motion
        header = motion = False
        for line in lines[0:20]:
            if line.lower().endswith("der staten-generaal"):
                header = True
                continue
            if "motie" in line.lower() or "amendement" in line.lower():
                motion = True
                break

        if not header or not motion:
            print "Invalid motion, stop processing"
            print self.text

        opening_offset = 1
        opening_number = None
        for opening_number, line in enumerate(lines):
            if line.startswith("gehoord de beraadslaging"):
                opening_number += opening_offset
                break

        closing_offset = 0
        closing_number = None
        for closing_number, line in enumerate(lines):
            if line.startswith("en gaat over tot de orde van de dag"):
                closing_number += closing_offset
                break

        try:
            motion_lines = lines[opening_number:closing_number]
        except IndexError:
            pass

        # Make last
        if motion_lines[-1][-1] in string.punctuation:
            motion_lines[-1] = motion_lines[-1][:-1]
        motion_lines[-1] += "."

        # The request in the motion is marked bold in Markdown
        first_request = True
        for request_number, line in enumerate(motion_lines):
            if line.startswith("verzoekt de") or line.startswith(
                    "spreekt uit"):

                motion_lines[request_number] = "**" + line

                if not first_request:
                    motion_lines[request_number - 1] += "**"

                first_request = False

        if not first_request:
            motion_lines[-1] = motion_lines[-1] + "**"

        self.text = "\n".join(motion_lines)
