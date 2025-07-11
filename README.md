
# Semi-Automatic Short Form Video Generator

+ Makes short form videos from twitch clips. Mainly works on gaming clips with webcam. You can choose a creator or twitch category, how many clips and the language of those clips. Then choose where the webcam of the clips are. When selecting, click on the webcam (the red rectangle shows the area it is going to select) and press q to confirm selection.
    

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`twitch_client_id`

`twitch_client_secret`

These can be obtained by creating a Developer Application (https://dev.twitch.tv/console/apps)

## Deployment

To deploy this project run

```bash
  python3 main.py
```

