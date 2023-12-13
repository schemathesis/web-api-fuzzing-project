# 1.15 release
ARG revision=a2db686a4ebfe9c626ac390f040b272e96ff51b9


FROM maven:eclipse-temurin as builder

RUN git clone https://github.com/EMResearch/EvoMaster.git /app

RUN cd /app \
    && git checkout $revision \
    && mvn clean install -DskipTests


FROM eclipse-temurin:17-jre-ubi9-minimal

LABEL name="EvoMaster" repo_url="https://github.com/EMResearch/EvoMaster" revision=$revision

COPY --from=builder /app/core/target/evomaster.jar /EvoMaster/evomaster.jar
COPY --chmod=744 entrypoint.sh /
ENTRYPOINT ["./entrypoint.sh"]
