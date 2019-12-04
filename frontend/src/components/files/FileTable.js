import React from 'react';
import PropTypes from 'prop-types';

import { useTable, useRowSelect } from 'react-table';

import { makeStyles } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import MaUTable from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';

const useStyles = makeStyles(theme => ({
  root: {
    padding: theme.spacing(3, 2)
  }
}));

function Table({ caption, columns, data, onSelectedRows }) {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
    selectedFlatRows,
    state: { selectedRowPaths }
  } = useTable(
    {
      columns,
      data
    },
    useRowSelect
  );

  const classes = useStyles();

  React.useEffect(() => {
    onSelectedRows(selectedFlatRows.map(r => r.original));
  }, [selectedFlatRows]);

  return (
    <Paper className={classes.root}>
      <Typography variant="h5" component="h3">
        {caption}
      </Typography>
      <MaUTable
        {...getTableProps()}
        className={classes.table}
        aria-label={`${caption}-table`}
      >
        <caption>{caption}</caption>
        <TableHead>
          {headerGroups.map((headerGroup, i) => (
            <TableRow {...headerGroup.getHeaderGroupProps()} key={i}>
              {headerGroup.headers.map((column, j) => (
                <TableCell {...column.getHeaderProps()} key={j}>
                  {column.render('Header')}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableHead>
        <TableBody {...getTableBodyProps()}>
          {rows.map((row, i) => {
            prepareRow(row);
            return (
              <TableRow {...row.getRowProps()} key={i}>
                {row.cells.map((cell, j) => {
                  return (
                    <TableCell {...cell.getCellProps()} key={j}>
                      {cell.render('Cell')}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </MaUTable>
      <p>Selected Rows: {selectedRowPaths.length}</p>
      <pre>
        <code>
          {JSON.stringify(
            {
              selectedRowPaths: [...selectedRowPaths.values()],
              'selectedFlatRows[].original': selectedFlatRows.map(
                d => d.original
              )
            },
            null,
            2
          )}
        </code>
      </pre>
    </Paper>
  );
}

Table.propTypes = {
  caption: PropTypes.string.isRequired,
  columns: PropTypes.array.isRequired,
  data: PropTypes.array.isRequired,
  onSelectedRows: PropTypes.func.isRequired
};

function FileTable({ caption, onSelectedRows, data }) {
  const columns = React.useMemo(
    () => [
      // Let's make a column for selection
      {
        id: 'selection',
        // The header can use the table's getToggleAllRowsSelectedProps method
        // to render a checkbox
        // eslint-disable-next-line react/prop-types, react/display-name
        Header: ({ getToggleAllRowsSelectedProps }) => (
          <div>
            <input type="checkbox" {...getToggleAllRowsSelectedProps()} />
          </div>
        ),
        // The cell can use the individual row's getToggleRowSelectedProps method
        // to the render a checkbox
        // eslint-disable-next-line react/prop-types, react/display-name
        Cell: ({ row }) => (
          <div>
            {/* eslint-disable-next-line react/prop-types */}
            <input type="checkbox" {...row.getToggleRowSelectedProps()} />
          </div>
        )
      },
      {
        Header: 'Name',
        columns: [
          {
            Header: 'Video Name',
            accessor: 'video_name'
          }
        ]
      },
      {
        Header: 'Info',
        columns: [
          {
            Header: 'Type',
            accessor: 'type'
          },
          {
            Header: 'Processing State',
            accessor: 'processing_state'
          }
        ]
      }
    ],
    []
  );

  return (
    <div>
      <CssBaseline />
      <Table
        caption={caption}
        columns={columns}
        data={data}
        onSelectedRows={onSelectedRows}
      />
    </div>
  );
}

FileTable.propTypes = {
  caption: PropTypes.string.isRequired,
  data: PropTypes.array.isRequired,
  onSelectedRows: PropTypes.func.isRequired
};

export default FileTable;
