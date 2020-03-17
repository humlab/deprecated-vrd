import React from 'react';
import PropTypes from 'prop-types';

import { useTable, useRowSelect, usePagination } from 'react-table';

import { makeStyles } from '@material-ui/core/styles';
import CssBaseline from '@material-ui/core/CssBaseline';
import MaUTable from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Toolbar from '@material-ui/core/Toolbar';
import Button from '@material-ui/core/Button';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';
import Input from '@material-ui/core/Input';

const useStyles = makeStyles(theme => ({
  root: {
    padding: theme.spacing(3, 2)
  },
  title: {
    flex: '1 1 100%'
  }
}));

function Table({ caption, columns, data, onSelectedRows }) {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    pageOptions,
    pageCount,
    selectedFlatRows,
    state: { selectedRowPaths, pageIndex, pageSize },
    gotoPage,
    previousPage,
    nextPage,
    setPageSize,
    canPreviousPage,
    canNextPage
  } = useTable(
    {
      columns,
      data
    },
    useRowSelect,
    usePagination
  );

  const classes = useStyles();

  React.useEffect(() => {
    onSelectedRows(selectedFlatRows.map(r => r.original));
  }, [selectedFlatRows]);

  return (
    <Paper className={classes.root}>
      <Toolbar>
        <Typography className={classes.title} variant="h5" id="tableTitle">
          {caption}
        </Typography>
      </Toolbar>
      <Divider />
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
          {page.map((row, i) => {
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
      <div className="pagination">
        <Button onClick={() => gotoPage(0)} disabled={!canPreviousPage}>
          {'<<'}
        </Button>{' '}
        <Button onClick={() => previousPage()} disabled={!canPreviousPage}>
          {'<'}
        </Button>{' '}
        <Button onClick={() => nextPage()} disabled={!canNextPage}>
          {'>'}
        </Button>{' '}
        <Button onClick={() => gotoPage(pageCount - 1)} disabled={!canNextPage}>
          {'>>'}
        </Button>{' '}
        <span>
          Page{' '}
          <strong>
            {pageIndex + 1} of {pageOptions.length}
          </strong>{' '}
        </span>
        <span>
          | Go to page:{' '}
          <Input
            type="number"
            defaultValue={pageIndex + 1}
            onChange={e => {
              const page = e.target.value ? Number(e.target.value) - 1 : 0;
              gotoPage(page);
            }}
            style={{ width: '100px' }}
          />
        </span>{' '}
        <Select
          value={pageSize}
          onChange={e => {
            setPageSize(Number(e.target.value));
          }}
        >
          {[10, 20, 30, 40, 50].map(pageSize => (
            <MenuItem key={pageSize} value={pageSize}>
              Show {pageSize}
            </MenuItem>
          ))}
        </Select>
      </div>

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
            accessor: 'display_name'
          }
        ]
      },
      {
        Header: 'Info',
        columns: [
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
