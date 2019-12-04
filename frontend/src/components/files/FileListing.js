import React from 'react';
import PropTypes from 'prop-types';

const FileListing = ({ filename, type, state }) => (
  <tr>
    <th scope="row">{filename}</th>
    <td>{type}</td>
    <td>{state}</td>
  </tr>
);

FileListing.propTypes = {
  filename: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  state: PropTypes.string.isRequired
};

export default FileListing;
