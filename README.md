# actionSHARK
### __Description__:
actionSHARK is developed to collect all actions from a GitHub repository using command line and save them to MongoDB.<br />
Actions in GitHub are divided to workflows, runs, jobs, and artifacts.
<br />
<br />
### __Installation__:
`pip install actionshark`
<br />
<br />

### __How to Run__:
Simple quick run for a local MongoDB:
<br />
`python main.py -o [owner] -r [repository]`
<br />
<br />

Specify a database username and password :
<br />
`python main.py -t [token] -o [owner] -r [repository] -U [username] -P [password] -DB [database]`
<br />
<br />
***

### __Command line arguments__:

You could run the following command:
<br />
`python main.py -h`
<br />
<br />

Or see to the list below:
| Parameter           | Short Form | Default | Required   | Description                                            |
| ------------------- | ---------- | ------- | ---------- | ------------------------------------------------------ |
| --token             | -t         | No      | None[1]    | GitHub token to authenticate user                      |
| --token-env         | -env       | No      | None[1]    | Environment variable, where token is stored            |
| --owner             | -o         | Yes     |            | Owner name of the repository                           |
| --repository        | -r         | Yes     |            | Repository Name                                        |
| --db-user           | -U         | No      | None[2]    | Database user name                                     |
| --db-password       | -P         | No      | None[2]    | Database user password                                 |
| --db-database       | -DB        | No      | smartshark | Database name                                          |
| --db-hostname       | -H         | No      | localhost  | Name of the host, where the database server is running |
| --db-port           | -p         | No      | 27017      | Port, where the database server is listening           |
| --db-authentication | -a         | No      |            | Name of the authentication database                    |
| --ssl               |            | No      | False      | Enables SSL                                            |
| --version           | -v         | No      |            | Shows the version                                      |
| --debug             |            | No      | DEBUG      | Sets the debug level                                   |

<br />
1: ActionShark will run without a token but the limit is much lower than with a token.
<br />
2: For a local MongoDB, username and password are optional.