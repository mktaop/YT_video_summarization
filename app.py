import streamlit as st, os, csv, pandas as pd
from pytube import YouTube
from serpapi import GoogleSearch
from openai import OpenAI


def setup():
    st.set_page_config(
        page_title="	✨ YouTube Video Summarization",
        layout="centered"
    )
    st.header(":sparkles: Summarize YouTube Videos", anchor=False, divider='orange')
    
    st.sidebar.header("About this app:", divider='rainbow')
    st.sidebar.write("1. Choose how you want to provide URL")
    st.sidebar.write("2. Provide LLM a prompt to summarize or answer question")
    with st.sidebar:
        st.divider()
    
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


def get_video_source():
    tip1 = "Use YouTube search option to find videos based on your search term, or directly enter or paste an url."
    choice = st.sidebar.radio(":red[Choose source for URL:]",
                              [":red[Use YouTube Search]", ":red[Directly Enter URL(s)]"],
                              help=tip1)
    return choice


def getgptresponse(client, model, temperature, message, streaming):
    try:
        response = client.chat.completions.create(model=model, messages=message, temperature=temperature, stream=streaming)

        output = response.choices[0].message.content
        tokens = response.usage.total_tokens
        yield output, tokens

    except Exception as e:
        print(e)
        yield ""
    

def main():
    setup()
    # Get the search term from the user that we pass to youtube search engine to retrieve results
    choice = get_video_source()
    if choice == ":red[Use YouTube Search]":
        url = st.text_input("Enter search term for YouTube search and hit enter.")
        if url:
            params = {
                      "engine": "youtube",
                      "search_query": f'{url}',
                      "api_key": f'{SERP_API_KEY}',
                      "num":  "10"
                    }

            search = GoogleSearch(params)
            results = search.get_dict()
            yt_results = results["video_results"]
            
            # Create a csv to store the results of the search
            with open('/Users/Documents/serpapi_ytresults.csv', 'w', newline='') as csvfile:
            	csv_writer = csv.writer(csvfile)
            	# Write the headers for the csv
            	csv_writer.writerow(["Title", "Link", "Length", "Published_date"])
            	# Write the data to csv, basically the search results
            	for result in yt_results:
            		csv_writer.writerow([result["title"], result["link"], result["length"], 
                                   result["published_date"]])
            # Read the file we just created based on search results
            df_yt = pd.read_csv('/Users/Documents/serpapi_ytresults.csv', index_col=0)
            # Show the top 10 results for the user to consider 
            st.write("Top 10 results from the search, copy the url of the video of interest:")
            st.dataframe(df_yt.head(10))
            st.divider()
            
            # Get the user to provide one or more urls from the search results displayed
            st.write("Provide an url from above list for the video you want a LLM to summarize the content of the video")
            yt_url=st.text_input("Paste or enter the YouTube URL you want to download and summarize.")
            if yt_url:
                # Following few lines will take the url(s) provided by user and scrape the audio and convert it to text
                yt = YouTube(f'{yt_url}')
                yt.streams.filter(only_audio=True).first().download(filename='/Users/Documents/trialmp.mp4')
                audio_file = open("/Users/Documents/trialmp.mp4", "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    response_format="text",  
                    file=audio_file
                )
                
                # Text we collected from above is then passed to a LLM 
                model = "gpt-3.5-turbo-0125" #if video is longer than an hour use 'gpt-4-turbo'
                prompt = st.text_input("Enter prompt for LLM, e.g. Summarize the following youtube transcript.")
                if prompt:
                    message=[]
                    message.append({"role": "system", "content": f"{prompt}"})
                    message.append({"role": "user", "content": f"{transcript}"})
                    for result in getgptresponse(client, model, temperature=0, message=message, streaming=False):
                        output = result[0]
                        st.write(output)
                        
    else:
        yt_url2=st.text_input("Paste or enter each YouTube URL you want to download audio for, separate urls with a space.")
        if yt_url2:
            urls = yt_url2.split(' ')
            zlen = len(urls)
            transcripts=[]
            for i in range(zlen):
                yt_url3 = urls[i]
                yt = YouTube(f'{yt_url3}')
                yt.streams.filter(only_audio=True).first().download(filename='/Users/Documents/trialmp.mp4')
                
                audio_file = open("/Users/Documents/trialmp.mp4", "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    response_format="text",  
                    file=audio_file
                )
                transcripts.append(transcript)
                
            model = "gpt-3.5-turbo-0125" #if video is longer than an hour use 'gpt-4-turbo'
            prompt2 = st.text_input("Enter prompt for LLM, e.g. Summarize the following youtube transcript.")
            if prompt2:
                message2=[]
                message2.append({"role": "system", "content": f"{prompt2}"})
                message2.append({"role": "user", "content": f"{transcripts}"})
                for result2 in getgptresponse(client, model, temperature=0, message=message2, streaming=False):
                    output2 = result2[0]
                    st.write(output2)
    
    
if __name__ == '__main__':
    SERP_API_KEY = os.environ.get('SERPAPI_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    client = OpenAI(api_key=OPENAI_API_KEY)
    main()
