import React, { Component } from 'react';

class Form extends Component {

  constructor(props) {
    super(props);
    this.state = {
      "search-type": "text-to-image",
      "model": "clip",
      "k-value": 100,
      "query": ""
    }
  }

  render() {
    return (
      <div class="center" style={{"max-width": "1000px", "margin": "0 auto", "padding-top": "10px", "padding-bottom": "10px"}}>
        <form class="form-inline" action="/search" method="post" style={{"max-width": "1000px", "margin": "0 auto"}} onSubmit={
          function(e) {
            console.log(e);
            e.preventDefault();
            this.props.submit_form(this.state);
          }.bind(this)
          }>
          <div class="row" style={{"max-width": "1000px", "margin": "0 auto", "padding-top": "10px", "padding-bottomA": "10px"}}>
            <div class="input-group">
              <input class="form-control" type="text" placeholder="text query for searching images" onChange={
                function(e) {
                  this.setState({'query': e.target.value});
                }.bind(this)
                }></input>
              <span class="search-btn">
                <button class="w-100 btn btn-lg btn-primary" type="submit">Search</button>
              </span>
            </div>
          </div>
          <div class="row" style={{"max-width": "1000px", "margin": "0 auto", "padding-top": "10px", "padding-bottom": "10px"}}>
            <div class="col-2" style={{"text-align": "center"}}>
              <label class="form-label" for="mclip_checkbox">Multilingual</label>
            </div>
            <div class="col-10" style={{"text-align": "center"}}>
              <label class="form-label" for="k_range_slider">k value: 100</label>
            </div>
          </div>
          <div class="row" style={{"max-width": "1000px", "margin": "0 auto", "padding-top": "10px", "padding-bottom": "10px"}}>
            <div class="col-2" style={{"text-align": "center"}}>
              <div class="col-1 form-check form-switch" style={{"display": "inline-block"}}>
                <input class="form-check-input" type="checkbox" data-toggle="tooltip" title="활성화할 경우, 한국어를 포함한 약 60가지의 다국어에 대해 pre-trained된 multilingual-CLIP의 text encoder를 사용합니다.<br>비활성화한 경우 영어에 대해서 pre-trained된 OpenAI CLIP의 text encoder를 사용합니다." onChange={
                  function(e) {
                    let model;
                    if (e.target.checked) {
                      model = "mclip";
                    }
                    else {
                      model = "clip";
                    }
                    this.setState({'model': model});
                  }.bind(this)
                  }></input>
              </div>
            </div>
            <div class="col-10" style={{"text-align": "center"}}>
              <div class="form-range" style={{"display": "inline-block"}}>
                <input type="range" class="form-range" min="10" max="500" value="100" step="10" data-toggle="tooltip" title="k개의 가장 비슷한 이미지를 검색합니다.<br>k값은 10~500 사이에서 선택 가능합니다." onChange={
                  function(e) {
                    console.log(e.target.value);
                  }.bind(this)
                  }></input>
              </div>
            </div>
          </div>
        </form>
      </div>
    );
  }

}

export default Form;
