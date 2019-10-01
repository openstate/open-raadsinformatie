import string

import bugsnag

from ocd_backend.enrichers.media_enricher.tasks.file_to_text import FileToText


class GegevensmagazijnMotionText(FileToText):
    def process_text(self, text, item):
        lines = text.split("\n")

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
            bugsnag.notify(
                "Invalid motion, stop processing: ",
                severity="info",
                meta_data={"text": text}
            )

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
            motion_lines = None

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
            motion_lines[-1] += "**"

        item.text = "\n".join(motion_lines)
