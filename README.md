# actionSHARK
### __Description__:
actionSHARK is developed to collect all actions from a GitHub repository using command line and save them to MongoDB.<br />
Actions in GitHub are divided to workflows, runs, jobs, and artifacts.
For more information about actions, please read the GitHub documentation [here](https://docs.github.com/en/actions).
<br />
<br />
### __Installation__:
Clone the repository
```
git clone https://github.com/smartshark/actionSHARK.git
```
Then change directory to "actionSHARK":
```
cd actionSHARK
```
<br />

### __How to Run__:
Simple quick run for a local MongoDB:
<br />
```
python main.py -ru [repository url]
```
OR
```
python main.py -o [owner] -r [repository]
```
<br />
<br />

Specify a database, username, and password :
<br />
```
python main.py -t [token] -ru [repository url] -U [username] -P [password] -DB [database]
```
<br />

### __Command line arguments__:

You could run the following command:
<br />
```
python main.py -h
```

| Parameter           | Short Form | Default    | Description                                            |
| ------------------- | ---------- | ---------- | ------------------------------------------------------ |
| --token             | -t         | None[1]    | GitHub token to authenticate user                      |
| --token-env         | -env       | None[1]    | Environment variable, where token is stored            |
| --owner             | -o         |            | Owner name of the repository                           |
| --repository        | -r         |            | Repository Name                                        |
| --url               | -ru        |            | Repository URL                                         |
| --db-user           | -U         | None[2]    | Database user name                                     |
| --db-password       | -P         | None[2]    | Database user password                                 |
| --db-database       | -DB        | smartshark | Database name                                          |
| --db-hostname       | -H         | localhost  | Name of the host, where the database server is running |
| --db-port           | -p         | 27017      | Port, where the database server is listening           |
| --db-authentication | -a         |            | Name of the authentication database                    |
| --ssl               |            | False      | Enables SSL                                            |
| --version           | -v         |            | Shows the version                                      |
| --debug             |            | DEBUG      | Sets the debug level                                   |

<br />
1: ActionShark will run without a token but the limit is much lower than with a token.
<br />
2: For a local MongoDB, username and password are optional.

***
