hello guys 
this is a project of rental car system, made with flask and mongodb
to run this code follow these steps

## Configuration
1- type **pip install requirements.txt**
2- now we need to generate a secret key to maintain a secret connexion between the code and mongodb
    a-open a any terminal where u can run a python code 
    b- run this 
        import secrets
        print(secrets.token_hex(32))  # Copiez la sortie dans .env
    c- go to a file called '.env', paste the output of the code in the variable called 'SECRET_KEY'
    d- go agin to another file called 'config.py' and paste the output in the variable called 'SECRET_KEY'
3- to run the project tap **"python run.py"**
