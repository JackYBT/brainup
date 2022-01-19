import zipfile
class ZipUtil():
    def get_zip(self,files,zip_path,zip_name):
        zp=zipfile.ZipFile(zip_path,'w', zipfile.ZIP_DEFLATED)
        for file in files:
            zp.write(file,arcname=zip_name)
        zp.close()
