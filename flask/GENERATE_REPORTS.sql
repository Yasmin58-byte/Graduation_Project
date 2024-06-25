create database GENERATE_REPORTS;
use GENERATE_REPORTS;
CREATE TABLE users (
   user_id INT PRIMARY KEY IDENTITY(1,1),
   username VARCHAR(255) NOT NULL,
   email VARCHAR(255) NOT NULL,
   password VARCHAR(255) NOT NULL,
   reset_token VARCHAR(255),
   reset_token_expiration DATETIME
);

CREATE TABLE projects (
    project_id INT PRIMARY KEY IDENTITY(1,1),
    project_name VARCHAR(255) NOT NULL,
    creation_date DATE DEFAULT GETDATE(),
    modification_date DATE,
    modified_by VARCHAR(255),
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


CREATE TABLE METADATA (
    Id INT PRIMARY KEY IDENTITY(1,1),   
	DatabaseName NVARCHAR(255),
    ColumnsNames NVARCHAR(MAX),   
	NumberOfColumns NVARCHAR(MAX),
    NumberOfRows NVARCHAR(MAX),
	Domain VARCHAR(1000)
    );


CREATE TABLE PROJECT_METADATA (
    PROJECT_ID INT,
    METADATA_ID INT,
    PRIMARY KEY (PROJECT_ID, METADATA_ID),
    CONSTRAINT FK_PROJECT_ID FOREIGN KEY (PROJECT_ID) REFERENCES PROJECTS(PROJECT_ID),
    CONSTRAINT FK_METADATA_ID FOREIGN KEY (METADATA_ID) REFERENCES METADATA(Id)
);

CREATE TABLE Report (
    report_id INT PRIMARY KEY IDENTITY,
    report_name VARCHAR(100) NOT NULL,
    report_description TEXT,
    report_domain VARCHAR(20),
	project_id int,
	user_id int
	FOREIGN KEY (user_id) REFERENCES users(user_id),
	FOREIGN KEY (project_id) REFERENCES projects(project_id)


);


-- Report predicts Metadata
CREATE TABLE ReportMetadata (
    report_id INT,
    metadata_id INT,
    PRIMARY KEY (report_id, metadata_id),
    FOREIGN KEY (report_id) REFERENCES Report(report_id),
    FOREIGN KEY (metadata_id) REFERENCES METADATA(Id)
);
SELECT * FROM METADATA

