hello guys 
this is a project of rental car system, made with flask and mongodb
to run this code follow these steps
## Configuration
1- type **pip install requirements.txt**<br>
2- now we need to generate a secret key to maintain a secret connexion between the code and mongodb<br>
    a-open a any terminal where u can run a python code <br>
    b- run this <br>
        import secrets<br>
        print(secrets.token_hex(32))  # Copiez la sortie dans .env<br>
    c- go to a file called '.env', paste the output of the code in the variable called 'SECRET_KEY'<br>
    d- go agin to another file called 'config.py' and paste the output in the variable called 'SECRET_KEY'<br>
3- to run the project tap **"python run.py"**
