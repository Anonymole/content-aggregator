# Content-Aggregator
--An AI-First built content scraper and aggretion app to create single file/epub/mobi/mp3 files from any textual content--
## BETA CODE
### This project was used initially to fetch a compendium of WordPress posts from an author and build a composite file to be used to create an EPub and/or Mobi file for easy reading on a mobile device. Instead of reading the posts, one-at-a-time, I wanted a means to read them like a novel.
### Thusly, Wordpress was the first target pursued as the source of content. However, other sources were planned, just not fleshed out.
#### NOTE: Cursor was used to write all the code in this project.
## Usage
- ### Fetch the repo
- ### Copy config.example.yaml to config.yaml
- ### Update config.yaml with your details of your book
- ### Uses PanDoc and Calibre to create .epub & .mobi files
- ### `> python main.py` will run and build your markdown, and mobile books
- ### MP3 is coming -- will need LLM integration
