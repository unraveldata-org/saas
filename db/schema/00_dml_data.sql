USE clm;

--Example of free trial request that will launch the entire pipeline.
INSERT INTO trial_request (first_name, last_name, email, title, company, ip, state, start_date, cloud_provider, create_cluster, notify_customer)
VALUES ('Alejandro', 'Fernandez', 'alejandro@unraveldata.com', 'Engineer', 'Unravel', '127.0.0.1', 'pending', UTC_TIMESTAMP(), 'EMR', TRUE, NULL);

INSERT INTO trial_request (first_name, last_name, email, title, company, ip, state, start_date, cloud_provider, create_cluster, notify_customer)
VALUES ('John', 'Doe', 'hacker@gmail.com', 'Hacker', 'HackBook', '127.0.0.1', 'denied', UTC_TIMESTAMP(), 'EMR', TRUE, NULL);
