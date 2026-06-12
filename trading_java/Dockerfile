# Stage 1: Το Build Environment (Έχει μέσα το Maven για να κάνει compile)
FROM maven:3.9-eclipse-temurin-17-alpine AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Το Production Environment (Πανάλαφρο, μόνο με το JRE)
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]











COPY xrysos_database ./xrysos_database
