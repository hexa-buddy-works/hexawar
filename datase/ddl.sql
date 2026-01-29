CREATE TABLE "sec_war_question" (
    "q_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "question" TEXT NOT NULL UNIQUE,
    "severity" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "VERSION" INTEGER 
);

CREATE TABLE "sec_war_quest_bece" (
    "bp_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "description" TEXT NOT NULL UNIQUE,
    "q_id" INTEGER NOT NULL,
    "aws_link" TEXT NOT NULL,
    "impl_type" TEXT NOT NULL,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "VERSION" INTEGER,
    FOREIGN KEY(q_id) REFERENCES sec_war_question(q_id) 
);

CREATE TABLE "sec_war_findings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "question" TEXT NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "aws_link" TEXT NOT NULL,
    "impl_type" TEXT NOT NULL,
    "violated_resources_count" INTEGER DEFAULT 0,
    "status" BOOLEAN,
    "created_at" TEXT DEFAULT CURRENT_TIMESTAMP,
    "VERSION" INTEGER
)