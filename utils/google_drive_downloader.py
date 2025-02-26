import gdown
import zipfile
import os
import re

class GoogleDriveDownloader:
    def __init__(self, gdrive_link: str, output_zip: str = "downloaded_file.zip", output_folder: str = "meta_data"):
        self.file_id = self.extract_file_id(gdrive_link)
        self.output_zip = output_zip
        self.output_folder = output_folder

    @staticmethod
    def extract_file_id(gdrive_link: str) -> str:
        """
        Extracts file ID from a Google Drive link.
        """
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', gdrive_link)
        if not match:
            raise ValueError("Invalid Google Drive link format.")
        return match.group(1)

    def download_file(self) -> str:
        """
        Downloads a file from Google Drive using the extracted file ID.
        """
        download_url = f"https://drive.google.com/uc?id={self.file_id}"
        gdown.download(download_url, self.output_zip, quiet=False)
        return self.output_zip

    def unzip_file(self) -> None:
        """
        Unzips the downloaded ZIP file to the specified output folder.
        """
        os.makedirs(self.output_folder, exist_ok=True)
        with zipfile.ZipFile(self.output_zip, 'r') as zip_ref:
            zip_ref.extractall(self.output_folder)
        print(f"Files extracted to: {self.output_folder}")

    def execute(self) -> None:
        """
        Orchestrates the download and extraction processes.
        """
        print("Starting download...")
        self.download_file()
        print("Download complete. Now unzipping...")
        self.unzip_file()
        print("Process finished!")

# if __name__ == "__main__":
#     # Example Google Drive link (replace with your own)
#     gdrive_link = "https://drive.google.com/file/d/1YqqfAdlAYJVBQMKtyBFU8uZk6ZehJnH_/view?usp=sharing"
#     downloader = GoogleDriveDownloader(gdrive_link)
#     downloader.execute()
