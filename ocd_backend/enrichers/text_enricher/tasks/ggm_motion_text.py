import string

import bugsnag

from ocd_backend.enrichers.text_enricher.tasks import BaseEnrichmentTask


class GegevensmagazijnMotionText(BaseEnrichmentTask):
    def enrich_item(self, item):
        if not hasattr(item, 'text'):
            return

        text = item.text
        if type(item.text) == list:
            text = ' '.join(text)

        if not text:
            return

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
            # bugsnag.notify(
            #     Exception("Invalid motion, stop processing"),
            #     severity="info",
            #     meta_data={"text": text}
            # )
            return

        lines = [x.strip() for x in lines]

        opening_offset = -1
        opening_number = None
        for opening_number, line in enumerate(lines):
            # De kamer
            # gehoord de beraadslaging
            if line.startswith("gehoord de beraadslaging"):
                opening_number += opening_offset
                break

        closing_offset = 1
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
        try:
            if motion_lines[-1][-1] in string.punctuation:
                motion_lines[-1] = motion_lines[-1][:-1]
            motion_lines[-1] += "."
        except IndexError:
            pass

        motion_lines = [x for x in motion_lines if not x.startswith('Tweede Kamer, vergaderjaar ')]

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

        if motion_lines:
            item.enriched_text = "  \n".join(motion_lines)
