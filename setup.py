import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

long_description = "A distributed testing framework"

print("packages: ",setuptools.find_packages())

setuptools.setup(
     name='ktf',  
     version='0.1.5',
     author="Samuel Kortas",
     author_email="samuel.kortas@gmail.com",
     description="A distributed testing framework",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/samkos/ktf",   
     packages=setuptools.find_packages(),
     scripts=['ktf/scripts/ktf'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     
     install_requires=['ClusterShell','six'],  # Optional

 )
