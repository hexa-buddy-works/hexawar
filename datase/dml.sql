INSERT INTO sec_war_question (question, severity)
VALUES('How do you securely operate your workload', 'High');
INSERT INTO sec_war_quest_bece (description, q_id, aws_link, impl_type)
VALUES ('Secure account root user and properties', 1, 'https://aws.amazon.com/premiumsupport/knowledge-center/root-user-secure/', 'Manual');
INSERT INTO sec_war_findings (q_id, bp_id, violated_resources_count, violated_resource_service, violated_resource_description, impl_status)
VALUES (1, 1, 1, 'IAM', 'Root user has not enabled MFA', 0);