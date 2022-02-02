FROM rocker/tidyverse:3.6.3
RUN apt-get --allow-releaseinfo-change update
RUN apt-get install -y python3-pip
RUN pip3 install requests requests-oauthlib itsdangerous
RUN apt-get install -y r-base
RUN apt-get install nano
RUN apt-get install -y texlive-latex-base texlive-latex-recommended texlive-fonts-recommended

# install and set up google-cloud-sdk
RUN apt-get install -y curl gnupg apt-transport-https ca-certificates && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && \
    apt-get update -y && \
    apt-get install google-cloud-sdk -y

# r setup
RUN R -e "install.packages('data.table', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('digest', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('R.utils', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('dplyr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('stringr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('tidyverse', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('tidyr', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('haven', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('rio', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('readxl', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('ggplot2', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('rmarkdown', repos = 'http://cran.us.r-project.org')"
RUN R -e "install.packages('tinytex', repos = 'http://cran.us.r-project.org'); tinytex::install_tinytex()"

RUN echo 'export PATH="$HOME/bin:$PATH"' >> /root/.bashrc

COPY ./bootstrap.sh /root
RUN chmod +x /root/bootstrap.sh

ENTRYPOINT [ "/bin/bash", "/root/bootstrap.sh" ]