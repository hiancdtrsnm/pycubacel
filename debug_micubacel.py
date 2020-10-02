import streamlit as st
from micubacel_manager import MiCubacel, BadCredentials
import requests

class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def transform(data):
    if isinstance(data, dict):
        res = dotdict()
        for i,j in data.items():
            res[i]=transform(j)
        return res
    return data

user = st.sidebar.text_input('Username')
passw = st.sidebar.text_input('Password', type="password")

mic = MiCubacel(user, passw)

if st.sidebar.button('Get Data'):
    try:
        data = mic.consult()
        data = transform(data)
        txt = f"""
        <html>
        <head>
            <style>
                td{{
                    border-bottom: 1px solid #333;
                    margin-left: 3px;
                    margin-right: 3px;
                }}
                thead, th {{
                    background-color: #333;
                    color: #fff;
                }}
                .bg {{
                    background-color: rgb(92, 92, 92);
                    color: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <table>
                    <thead>
                        <tr>
                            <th colspan="3">Internet</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="bg">Service</td>
                            <td class="bg">Value</td>
                        </tr>
                        <tr>
                            <td>LTE only</td>
                            <td id='lteo'>{data.data['values'].only_lte.cant} MB</td>
                        </tr>
                    <tr>
                            <td>All networks</td>
                            <td id='an'>{data.data['values'].all_networks.cant} MB</td>
                        </tr>
                    <tr>
                            <td>LTE Bonus</td>
                            <td id='lteb'>{data.data['values'].lte.cant} MB</td>
                        </tr>
                    <tr>
                            <td>National Bonus</td>
                            <td id='nb'>{data.data['values'].national_data.cant} MB</td>
                        </tr>
                    </tbody>
                </table>
                <br>
                <table>
                    <thead>
                        <tr>
                            <th colspan="3">General</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="bg">Service</td>
                            <td class="bg">Value</td>
                        </tr>
                        <tr>
                            <td>Credit</td>
                            <td id='cerdit'>{data.credit['values'].credit_normal.cant}</td>
                        </tr>
                    <tr>
                            <td>Credit Bonus</td>
                            <td id='cerditb'>{data.credit['values'].credit_bonus.cant}</td>
                        </tr>
                    <tr>
                            <td>Minute</td>
                            <td id='min'>{data.others['values'].minutes.delta}</td>
                        </tr>
                    <tr>
                            <td>SMS</td>
                            <td id='sms'>{data.others['values'].sms.delta}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </body>
        """

        st.markdown(txt, unsafe_allow_html = True)
    except BadCredentials:
        st.warning('Bad Crdentials')
    except requests.ConnectionError:
        st.warning('Connection Error')
