# Lab Submission Instruction

## Student Details and Individual Member Contributions

**Name of the team on GitHub Classroom:**

**Member 1:**

| **Details**                                                                                                                           | **Comment** |
|:--------------------------------------------------------------------------------------------------------------------------------------|:------------|
| **Student ID**                                                                                                                        |             |
| **Name**                                                                                                                              |             |
| **What part of the lab did you personally<br/>contribute to (provide a link to the<br/>branch(es)), and what did you learn from it?** |             |

**Member 2:**

| **Details**                                                                                                                           | **Comment** |
|:--------------------------------------------------------------------------------------------------------------------------------------|:------------|
| **Student ID**                                                                                                                        |             |
| **Name**                                                                                                                              |             |
| **What part of the lab did you personally<br/>contribute to (provide a link to the<br/>branch(es)), and what did you learn from it?** |             |

**Member 3:**

| **Details**                                                                                                                           | **Comment** |
|:--------------------------------------------------------------------------------------------------------------------------------------|:------------|
| **Student ID**                                                                                                                        |             |
| **Name**                                                                                                                              |             |
| **What part of the lab did you personally<br/>contribute to (provide a link to the<br/>branch(es)), and what did you learn from it?** |             |

**Member 4:**

| **Details**                                                                                                                           | **Comment** |
|:--------------------------------------------------------------------------------------------------------------------------------------|:------------|
| **Student ID**                                                                                                                        |             |
| **Name**                                                                                                                              |             |
| **What part of the lab did you personally<br/>contribute to (provide a link to the<br/>branch(es)), and what did you learn from it?** |             |

**Member 5:**

| **Details**                                                                                                                           | **Comment** |
|:--------------------------------------------------------------------------------------------------------------------------------------|:------------|
| **Student ID**                                                                                                                        |             |
| **Name**                                                                                                                              |             |
| **What part of the lab did you personally<br/>contribute to (provide a link to the<br/>branch(es)), and what did you learn from it?** |             |

## Video Demonstration

Submit the link to a short video (not more than 5 minutes) demonstrating your solution. Please ensure that the lecturer has rights to view the video.

Note that you are required to submit the link to the video and NOT the video itself. The video should NOT be uploaded to your repository—that would be a misuse of GitHub.

**Link to the video:**

---

## Questions

1. **Modify the transformation.** Add a new computed field to the
   transformer, for example `item_category` that classifies items into
   groups (e.g., "Meat-Based Dishes" vs "Vegetable-Based Dishes"). Rebuild the
   transformer container and verify the new field appears in ClickHouse.

2. **Write an analytical query.** Using the ClickHouse CLI, write a
   query that answers: "Which item has the highest total quantity
   ordered?" Use `GROUP BY` and `ORDER BY`.

3. **Measure pipeline latency.** Run the latency query from Step 5.
   What is the average delay between an order being inserted into
   PostgreSQL (`received_at`) and arriving in ClickHouse
   (`processed_at`)? What does this tell you about the pipeline?

4. **Inspect the replication slot.** Debezium creates a PostgreSQL
   replication slot to track its position in the WAL. Inspect it:

    ```bash
       docker exec -it postgres psql -U lab_user -d lab_db \
         -c "SELECT slot_name, plugin, active, restart_lsn FROM pg_replication_slots;"
    ```
   What happens to this slot if the Debezium connector is stopped?
   What risk does an unused replication slot pose to the database?
   (Hint: search for "PostgreSQL replication slot WAL accumulation".)

5. **Stop a Kafka broker.** Run `docker stop kafka3` while the pipeline
   is running. Observe that the producer, consumers, and transformer
   all continue operating. Then run `docker start kafka3` and watch the
   broker rejoin the cluster. This is the same fault tolerance exercise
   from Part 2 — verify it still holds in the more complex Part 3 setup.