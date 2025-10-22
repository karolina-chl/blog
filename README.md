# Blogging platform
This blogging platform implementation allows for the following user stories: 
1. Publishing a post
2. Editing a post
3. Browse my own posts
4. Delete a post
5. See all posts

# Demo
Follow this demo to test the code. 
## 0. Set up your uv venv
To set up your environment with uv run: 
`uv venv` and then 
`uv pip install -r requirements.txt`

## 1. Start
In your terminal run: 
`uv run app.py`

## 2. Create a post
To create a post run the following command: 
`uvx --from httpie http POST :5000/posts author_id:=1 title="First post"  body="Hello, world"`
You can adjust author id, title and body to you liking. 

## 3. Edit my post
To edit a post run the following command: 
uvx --from httpie http PUT :5000/posts/1 author_id:=1 title="First post (edited)" body="Hello again"
You can only edit your own posts. 

## 4. Delete my post 
To delete a post run the following command:
`uvx --from httpie http -v DELETE :5000/posts/1 author_id:=1`

## 5. See all posts 
To see all posts run the following command:
`uvx --from httpie http :5000/posts`

## 6. See my posts 
To see my posts run the following command:
`uvx --from httpie http :5000/posts`

