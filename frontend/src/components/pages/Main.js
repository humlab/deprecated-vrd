import React, { useEffect, useState } from 'react';

import Dropzone from 'react-dropzone-uploader';
import { ToastContainer, toast } from 'react-toastify';

import axios from 'axios';
import openSocket from 'socket.io-client';

import { makeStyles } from '@material-ui/core/styles';
import FileTable from '../files/FileTable';
import Visualization from '../visualize/Visualization';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import Paper from '@material-ui/core/Paper';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import Divider from '@material-ui/core/Divider';
import Toolbar from '@material-ui/core/Toolbar';

const useStyles = makeStyles(theme => ({
  root: {
    padding: theme.spacing(3, 2)
  },
  title: {
    flex: '1 1 100%'
  }
}));

const socket = openSocket(`${process.env.REACT_APP_API_URL}`);

export default function Main() {
  const [allFiles, setAllFiles] = useState({});
  const [selectedQueryFiles, setSelectedQueryFiles] = useState([]);
  const [selectedReferenceFiles, setSelectedReferenceFiles] = useState([]);
  const [events, setEvents] = useState([]);
  const [activeComparisons, setActiveComparisons] = useState([]);

  useEffect(() => {
    listFiles();
    socket.on('video_file_added', videoFileAdded);
    socket.on('video_file_fingerprinted', videoFileFingerprinted);
    socket.on(
      'comparison_computation_completed',
      comparisonComputationCompleted
    );

    return () => {
      socket.off('video_file_added');
      socket.off('video_file_fingerprinted');
      socket.off('comparison_computation_completed');
    };
  }, []);

  const comparisonComputationCompleted = response => {
    const { query_video_name, reference_video_name } = response;
    const event = `Comparison ${query_video_name}:${reference_video_name} complete`;
    setEvents(events => [event, ...events]);
    toast.success(event);
  };

  const listFiles = async () => {
    // Fetch the file list, which is a bunch of
    // key-value pairs on the form,
    //
    // {"files": [{"processing_state": "FINGERPRINTED", "video_name": "Megamind.avi", ...}, {...}]}
    //
    // and a few other attributes
    const { data } = await axios.get(
      `${process.env.REACT_APP_API_URL}/api/files/list`
    );

    const files = data.files || [];

    // Make it so that the video_name is the key to the rest of the attributes,
    //
    // {"Megamind.avi": {"processing_state": "FINGERPRINTED", ...}
    const nameToObjList = files.map(obj => ({
      [obj.video_name]: obj
    }));

    const nameToObjDictionary = nameToObjList.reduce((map, x) => {
      Object.keys(x).forEach(key => {
        map[key] = x[key];
      });

      return map;
    }, {});

    // And overlay it with the previous state.
    //
    // The syntax "{ ...o1, ...o2 }" will overwrite the values in
    // o1 with the values in o2 if there are overlapping keys
    setAllFiles(allFiles => ({
      ...allFiles,
      ...nameToObjDictionary
    }));
  };

  const videoFileAdded = response => {
    setEvents(events => [`${response.display_name} added`, ...events]);
    setAllFiles(allFiles => ({
      ...allFiles,
      [response.video_name]: response
    }));
  };

  const videoFileFingerprinted = response => {
    const event = `${response.display_name} fingerprinted`;
    toast.info(event);
    setEvents(events => [event, ...events]);
    setAllFiles(allFiles => ({
      ...allFiles,
      [response.video_name]: response
    }));
  };

  const getUploadParams = ({ file, meta }) => {
    console.log(meta);
    const body = new FormData();

    body.append('file', file);
    body.append('file_type', 'QUERY');

    return { url: `${process.env.REACT_APP_API_URL}/api/files/upload`, body };
  };

  const handleChangeStatus = ({ meta, remove }, status) => {
    const errorStates = [
      'error_file_size',
      'error_validation',
      'error_upload_params',
      'exception_upload',
      'error_upload'
    ];

    if (status === 'headers_received') {
      toast.success(`${meta.name} uploaded!`);
      // Note: backend emits a state change after upload is accepted, no need to do anything
      remove();
    } else if (status === 'aborted') {
      toast.warn(`${meta.name}, upload aborted...`);
    } else if (errorStates.includes(status)) {
      toast.error(`${meta.name}, upload failed... status=${status}`);
    }
  };

  const getVideoNames = files => {
    return files.map(f => f.video_name);
  };

  const onCompareSelectionSubmitHandler = e => {
    e.preventDefault();

    axios
      .post(`${process.env.REACT_APP_API_URL}/api/fingerprints/compare`, {
        query_video_names: getVideoNames(selectedQueryFiles),
        reference_video_names: getVideoNames(selectedReferenceFiles)
      })
      .then(response => {
        console.log(response.data);

        for (let [k, v] of Object.entries(response.data)) {
          console.log(v);
          if (v === 'started') {
            toast.success(`Comparison between ${k} has been queued`);
          }
          if (v === 'exists') {
            toast.info(`Comparsion between ${k} already exists`);
          }
          if (v === 'fingerprint missing') {
            toast.warn(`${k} has not been fingerprinted yet. Try again later!`);
          }
        }
      });
  };

  const onViewComparisons = e => {
    e.preventDefault();

    axios
      .post(`${process.env.REACT_APP_API_URL}/api/fingerprints/comparisons`, {
        query_video_names: getVideoNames(selectedQueryFiles),
        reference_video_names: getVideoNames(selectedReferenceFiles)
      })
      .then(response => {
        setActiveComparisons(response.data.comparisons);
      });
  };

  const memoizedVideoFiles = React.useMemo(() => Object.values(allFiles), [
    allFiles
  ]);

  const classes = useStyles();

  const createVisualizationsForComparisons = () => {
    const visualizations = [];

    activeComparisons.forEach(comparison => {
      console.log(
        `Rendering comparison between ${comparison.queryVideoName} and ${comparison.referenceVideoName}`
      );
      visualizations.push(
        <Visualization
          key={comparison.queryVideoName + comparison.referenceVideoName}
          comparison={comparison}
        />
      );
    });

    return visualizations;
  };

  return (
    <div>
      <div className="row">
        <div className="col">
          <Dropzone
            getUploadParams={getUploadParams}
            onChangeStatus={handleChangeStatus}
            styles={{
              dropzoneActive: { borderColor: 'green' }
            }}
          />
          <ToastContainer />
        </div>
      </div>
      <div className="row mt-5">
        <div className="col">
          <Grid container justify="center" wrap="nowrap" spacing={1}>
            <Grid item>
              <FileTable
                caption={'Query'}
                data={memoizedVideoFiles}
                onSelectedRows={setSelectedQueryFiles}
              />
            </Grid>
            <Grid item>
              <FileTable
                caption={'Reference'}
                data={memoizedVideoFiles}
                onSelectedRows={setSelectedReferenceFiles}
              />
            </Grid>
            <Grid item>
              <Paper className={classes.root}>
                <List>
                  <Toolbar>
                    <Typography
                      className={classes.title}
                      variant="h5"
                      id="tableTitle"
                    >
                      Events
                    </Typography>
                  </Toolbar>
                  <Divider />
                  {events.map((e, i) => (
                    <ListItem key={i} dense>
                      <ListItemText primary={`${e}`} />
                      <Divider />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
          <Button
            variant="contained"
            color="primary"
            onClick={onCompareSelectionSubmitHandler}
          >
            Compute Comparisons Between Selected
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={onViewComparisons}
          >
            View Comparisons Between Selected
          </Button>
        </div>
        {createVisualizationsForComparisons()}
      </div>
    </div>
  );
}
