CREATE TABLE learning_progress (id TEXT PRIMARY KEY NOT NULL,revision INTEGER NOT NULL,body TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE workspace_chunks (owner TEXT NOT NULL,token TEXT NOT NULL,seq INTEGER NOT NULL,body TEXT NOT NULL,PRIMARY KEY(owner,token,seq));
