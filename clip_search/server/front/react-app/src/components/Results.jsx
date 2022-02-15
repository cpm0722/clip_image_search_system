import React, { Component } from 'react';

class Results extends Component {

  constructor(props) {
    super(props);
    this.state = {
    }
  }

  render() {
    if (this.props.results.length != 0) {
      let imageArray = this.props.results['path'];
      let scoreArray = this.props.results['score'];
      let datasetArray = this.props.results['dataset'];
      let indexArray = this.props.results['index'];

      let gallerys = []
      for (let i = 0; i < imageArray.length; i++) {
        gallerys.push(
        <div class="col-lg-4 col-md-4 col-xs-6 thumb" data-toggle="tooltip" style={ {"white-space": "pre-line"} } data-html="true" title={ "Score: " + scoreArray[i].toPrecision(5) + "<br>dataset: " + datasetArray[i] }>
            <a href={ imageArray[i] } data-fancybox="gallery" title={ "dataset: " + datasetArray[i] } data-caption={ this.props.query }>
              <img src={ imageArray[i] } class="zoom img-fluid"></img>
            </a>
        </div>
        );
      }
      return (
        <div class="container page-top">
          <div class="row">
            { gallerys }
          </div>
        </div>
      );
    }
    else {
      return (
        <div class="container page-top">
        </div>
      );
    }
  }

}

export default Results;
