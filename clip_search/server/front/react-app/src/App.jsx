import React, { Component } from 'react';
import './css/App.css';
import Form from './components/Form';
import Results from './components/Results';
import axios from 'axios';

class App extends Component {

  constructor(props) {
    super(props);
    this.state = {
      'query': "",
      'results': [],
    }
  }

  update_state(search_type="", model="", k_value=100, query="") {
    this.setState({'search-type': search_type});
    this.setState({'model': model});
    this.setState({'k-value': k_value});
    this.setState({'query': query});
  }

  async submit_form(state) {
    console.log(state);
    if (state.query.length > 0) {
      try {
        const response = await axios.post(
          '/searches/text-to-images',
          {input_text: state['query'], k: state['k-value'], mclip: state['model']=='mclip'},
        );
        console.log(response);
        this.setState({'results': response['data']});
      } catch(error) {
        console.log(error);
      }
    }
  }

  render() {
    return (
      <div className="App">

        <div style={{"max-width": "1000px", "margin": "0 auto", "padding-top": "50px", "padding-bottom": "50px", "text-align": "center"}}>
          <h1 class="h2 mb-3 fw-bold">CLIP Image Search System</h1>
        </div>

        <Form submit_form={ this.submit_form.bind(this) }></Form>

        <Results query={this.state['query']} results={this.state['results']} ></Results>

      </div>
    );
  }
}

export default App;
