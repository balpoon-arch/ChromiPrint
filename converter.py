import asyncio
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright
import os

class HTMLToPDFConverter:
    def __init__(self, output_dir_name="Converted"):
        self.output_dir_name = output_dir_name
        
    def _get_file_uri(self, filepath: str | Path) -> str:
        """Converts a local path to a file URI."""
        path = Path(filepath).resolve()
        return path.as_uri()

    async def convert_batch(self, file_paths: list[str | Path], 
                            progress_callback=None,
                            log_callback=None,
                            print_background=True):
        """Converts a list of HTML files to PDF concurrently where possible or sequentially."""
        
        if not file_paths:
            if log_callback:
                log_callback("No files to convert.")
            return

        # Prepare output directory based on the first file's location
        # Assumes batch drag-and-drop generally comes from same area, or we can just use the first file's parent
        base_dir = Path(file_paths[0]).parent
        output_dir = base_dir / self.output_dir_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        total_files = len(file_paths)
        if log_callback:
            log_callback(f"Starting batch conversion of {total_files} files...")
            log_callback(f"Output directory: {output_dir}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create a reusable browser context
            context = await browser.new_context()

            completed = 0
            
            for index, file_path in enumerate(file_paths):
                path_obj = Path(file_path)
                output_pdf_path = output_dir / f"{path_obj.stem}.pdf"
                
                if log_callback:
                    log_callback(f"[{index+1}/{total_files}] Processing: {path_obj.name}")
                
                page = None
                try:
                    page = await context.new_page()
                    file_uri = self._get_file_uri(path_obj)
                    
                    # wait_until="networkidle" ensures all resources (images, JS) are loaded
                    await page.goto(file_uri, wait_until="networkidle")
                    
                    # Generate PDF with A4 format
                    await page.pdf(
                        path=str(output_pdf_path),
                        format="A4",
                        print_background=print_background
                    )
                    
                    if log_callback:
                        log_callback(f"  -> Success: Saved to {output_pdf_path.name}")
                        
                except Exception as e:
                    if log_callback:
                        log_callback(f"  -> Error converting {path_obj.name}: {str(e)}")
                finally:
                    if page:
                        await page.close()
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_files)

            await browser.close()
            
        if log_callback:
            log_callback("Batch conversion finished!")

# For testing this module directly
async def main():
    import sys
    if len(sys.argv) > 1:
        converter = HTMLToPDFConverter()
        def pcb(c, t): print(f"Progress: {c}/{t}")
        def lcb(msg): print(msg)
        await converter.convert_batch(sys.argv[1:], progress_callback=pcb, log_callback=lcb)

if __name__ == "__main__":
    asyncio.run(main())
