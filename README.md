# Kafka

| Key             | Value                                                                                                                                                                                                                                                                                     |
|:----------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Course Code** | BBT 4106                                                                                                                                                                                                                                                                                  |
| **Course Name** | BBT 4106: Business Intelligence I (Week 1-3)                                                                                                                                                                                                                                              |
| **Semester**    | April to July 2026                                                                                                                                                                                                                                                                        |
| **Lecturer**    | Allan Omondi                                                                                                                                                                                                                                                                              |
| **Contact**     | aomondi@strathmore.edu                                                                                                                                                                                                                                                                    |
| **Note**        | The lecture contains both theory and practice.<br/>This notebook forms part of the practice.<br/>It is intended for educational purposes only.<br/>Recommended citation: [BibTex](https://raw.githubusercontent.com/course-files/ServingMLModels/refs/heads/main/RecommendedCitation.bib) |

## Technology Stack

<p align="left">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/apachekafka/apachekafka-original-wordmark.svg" width="40" />
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" width="40"/>
</p>

## Repository Structure

```text
.
├── 1_kafka_fundamentals
│   ├── consumer_order_inventory.py
│   ├── consumer_order_notification.py
│   ├── docker-compose.yaml
│   ├── instructions_for_project_setup.md
│   ├── producer_order.py
│   └── requirements.txt
├── 2_containerized_microservices
│   ├── consumer-inventory
│   │   ├── Dockerfile.consumer-inventory
│   │   ├── consumer_order_inventory.py
│   │   ├── models.py
│   │   └── requirements.txt
│   ├── consumer-notification
│   │   ├── Dockerfile.consumer-notification
│   │   ├── consumer_order_notification.py
│   │   └── requirements.txt
│   ├── database
│   │   └── init.sql
│   ├── docker-compose.yaml
│   ├── instructions_for_project_setup.md
│   ├── producer
│   │   ├── Dockerfile.producer
│   │   ├── producer_order.py
│   │   └── requirements.txt
│   ├── project_cleanup.sh
│   └── project_setup.sh
├── LICENSE
├── README.md
└── admin_instructions
    ├── instructions_for_postlab_cleanup.md
    ├── instructions_for_project_setup.md
    └── instructions_for_python_installation.md

8 directories, 26 files
```

## Setup Instructions

- [Setup Instructions](./admin_instructions/instructions_for_project_setup.md)

## Lab Manual

Refer to the files below, in the order specified, for more details:

1. [Part 1: Kafka Fundamentals](1_kafka_fundamentals/instructions_for_project_setup.md)
2. [Part 2: Containerized Microservices](2_containerized_microservices/instructions_for_project_setup.md)
3. [Part 3: Data Engineering using Kafka](3_data_engineering/instructions_for_project_setup.md)

## Lab Submission Instructions

- [Lab Submission Instructions](lab_submission_instructions.md)

## Cleanup Instructions (to be done after submitting the lab)

- [Cleanup Instructions](/admin_instructions/instructions_for_postlab_cleanup.md)
