# Sometimes a Celery task hangs many hours on processing a PDF, caused by inefficient
# processing in pymupdf4llm. We can find out which PDF it is hanging on by checking
# the logs. When a PDF has been processed the log contains:
#   - a line with "Processed <n> pages to text for <pdf_name>"
#   - a line with "Processed <n> pages to markdown for <pdf_name>"
# If the markdown result is empty, OCR will be tried.
#
# When a PDF is hanging, the first "Processed..." line will be present,
# but the markdown result will be missing.
#
# This script finds these hanging PDFs in the log specified at the bottom.
#
import re
import json

class FindHangingPdfs:
    def find(self, file_name):
        pdfs = self.get_results(file_name)

        hanging_pdfs = self.clean_results(pdfs)
        print(json.dumps(hanging_pdfs, indent = 2))

    def get_results(self, file_name):
        pdfs = {}
        with open(file_name, 'r') as f:
            for line in f:
                start_line = re.search("pages to text for (.*)", line)
                if start_line:
                    pdf_name = start_line.group(1)
                    pdfs[pdf_name] = {}

                markdown_line = re.search("pages to markdown for (.*)", line)
                if markdown_line:
                    pdf_name = markdown_line.group(1)
                    if not pdf_name in pdfs:
                        continue

                    pdfs[pdf_name]['markdown'] = True

                empty_line = re.search("Parse result is empty for ([^,]*),", line)
                if empty_line:
                    pdf_name = empty_line.group(1)
                    if not pdf_name in pdfs:
                        continue

                    pdfs[pdf_name]['markdown'] = False
                    pdfs[pdf_name]['start_ocr'] = True

                ocr_line = re.search("pages using OCR for (.*)", line)
                if ocr_line:
                    pdf_name = ocr_line.group(1)
                    if not pdf_name in pdfs:
                        continue

                    pdfs[pdf_name]['ocr'] = True

        print(f"\nNumber of pdfs: {len(pdfs)}")
        return pdfs

    def clean_results(self, pdfs):
        hanging_pdfs = {}
        for pdf_name, results in pdfs.items():
            if not 'markdown' in results:
                hanging_pdfs[pdf_name] = results
                continue
            
            if not results['markdown']:
                if not 'ocr' in results:
                    hanging_pdfs[pdf_name] = results

        print(f"\nNumber of hanging pdfs: {len(hanging_pdfs)}")
        return hanging_pdfs

file_name = "ori.log.1"
FindHangingPdfs().find(file_name)    
