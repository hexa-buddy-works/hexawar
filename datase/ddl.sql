CREATE TABLE "sec_war_question" (
    "q_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "question" TEXT NOT NULL UNIQUE,
    "severity" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "version" INTEGER DEFAULT 1 
);

CREATE TABLE "sec_war_quest_bece" (
    "bp_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "description" TEXT NOT NULL UNIQUE,
    "q_id" INTEGER NOT NULL,
    "aws_link" TEXT NOT NULL,
    "impl_type" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "version" INTEGER DEFAULT 1 ,
    FOREIGN KEY(q_id) REFERENCES sec_war_question(q_id) 
);

CREATE TABLE "sec_war_findings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "q_id" INTEGER NOT NULL,
    "bp_id" INTEGER NOT NULL,
    "violated_resources_count" INTEGER DEFAULT 0,
    "violated_resource_service" TEXT NOT NULL,
    "violated_resource_description" TEXT NOT NULL,
    "impl_status" BOOLEAN,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "version" INTEGER DEFAULT 1,
    FOREIGN KEY(q_id) REFERENCES sec_war_question(q_id),
    FOREIGN KEY(bp_id) REFERENCES sec_war_quest_bece(bp_id)
)